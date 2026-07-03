import re
from datetime import datetime, timedelta, timezone
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers.search import SearchStates
from app.database.models import EpisodeCache, DownloadCache
from app.services.scraper import search_anime_scraper, get_episodes_scraper, get_download_links_scraper
from app.services.downloader import process_and_send_video
from app.utils.logging_config import logger

router = Router(name="download")

CACHE_EXPIRATION_HOURS = 24

@router.message(SearchStates.waiting_for_episode)
async def process_episode_selection(message: Message, db_session: AsyncSession, state: FSMContext):
    """
    Handles user entering episode numbers. Scrapes episodes,
    verifies if requested episode exists, resolves mirror download links,
    and displays quality options.
    """
    requested_ep = message.text.strip()
    
    # Retrieve stored search details
    state_data = await state.get_data()
    anilist_id = state_data.get("anilist_id")
    anime_title = state_data.get("anime_title")
    title_romaji = state_data.get("title_romaji")
    title_english = state_data.get("title_english")
    
    if not anilist_id:
        logger.error("Error in process: FSM state context lost during episode selection.")
        await message.answer("❌ Error: Lost state context. Please search for your anime again.")
        await state.clear()
        return

    logger.info(f"Starting episode resolution for '{anime_title}' (AniList ID: {anilist_id}, Episode: {requested_ep})")

    # Status notification
    status_msg = await message.answer("🔍 Checking episode list...")
    
    try:
        # Check database EpisodeCache first
        stmt = select(EpisodeCache).where(EpisodeCache.anilist_id == anilist_id)
        res = await db_session.execute(stmt)
        cached_episodes = res.scalars().all()
        
        episodes_list = []
        
        # If cached and not expired
        if cached_episodes and (datetime.now(timezone.utc) - cached_episodes[0].created_at) < timedelta(hours=CACHE_EXPIRATION_HOURS):
            logger.info(f"Episode list cache hit for AniList ID: {anilist_id}")
            episodes_list = [
                {"ep_number": ep.ep_number, "play_url": ep.play_url}
                for ep in cached_episodes
            ]
        else:
            logger.info(f"Episode list cache miss or expired for AniList ID: {anilist_id}. Scraping page...")
            # Need to scrape from AniNeko
            # 1. Search anime on scraper to get slug
            search_title = title_romaji or title_english
            scraper_results = await search_anime_scraper(search_title)
            
            if not scraper_results:
                if title_english and title_english != title_romaji:
                    logger.info(f"Romaji search failed. Retrying search with English title: {title_english}")
                    scraper_results = await search_anime_scraper(title_english)
                    
            if not scraper_results:
                logger.warning(f"Could not find anime '{search_title}' on AniNeko mirrors.")
                await status_msg.edit_text("❌ Could not find this anime on the streaming server mirrors.")
                await state.clear()
                return
                
            # Pick first/best result slug
            anime_slug = scraper_results[0]["slug"]
            logger.info(f"Matched anime slug on AniNeko: '{anime_slug}'")
            
            # 2. Get list of episodes
            scraped_eps = await get_episodes_scraper(anime_slug)
            if not scraped_eps:
                logger.error(f"Failed to parse episode list for slug: {anime_slug}")
                await status_msg.edit_text("❌ Failed to parse episode list from mirror.")
                await state.clear()
                return
                
            episodes_list = scraped_eps
            
            # 3. Update Cache
            # Clear old cache
            if cached_episodes:
                logger.info(f"Deleting expired episode cache for AniList ID: {anilist_id}")
                for old_ep in cached_episodes:
                    await db_session.delete(old_ep)
            
            # Insert new episodes
            logger.info(f"Caching {len(episodes_list)} parsed episodes for AniList ID: {anilist_id}")
            for ep in episodes_list:
                db_ep = EpisodeCache(
                    anilist_id=anilist_id,
                    ep_number=ep["ep_number"],
                    play_url=ep["play_url"]
                )
                db_session.add(db_ep)
            await db_session.commit()
            
        # Match user's input with the episodes list
        matched_ep = None
        norm_req = requested_ep.lstrip("0") or "0"
        
        for ep in episodes_list:
            norm_ep = ep["ep_number"].lstrip("0") or "0"
            if norm_req == norm_ep or requested_ep == ep["ep_number"]:
                matched_ep = ep
                break
                
        if not matched_ep:
            logger.info(f"Episode {requested_ep} not found in the parsed list.")
            ep_numbers = [e["ep_number"] for e in episodes_list]
            if len(ep_numbers) > 10:
                available_range = f"from `{ep_numbers[0]}` to `{ep_numbers[-1]}`"
            else:
                available_range = ", ".join([f"`{n}`" for n in ep_numbers])
                
            await status_msg.edit_text(
                f"❌ Episode `{requested_ep}` not found.\n"
                f"Available episodes: {available_range}.\n\n"
                f"🔢 **Please enter a valid episode number:**",
                parse_mode="Markdown"
            )
            return

        # Episode matched, get download mirrors
        play_url = matched_ep["play_url"]
        logger.info(f"Matched Episode {matched_ep['ep_number']}: Play page is {play_url}")
        
        # Check download cache
        dl_stmt = select(DownloadCache).where(DownloadCache.play_url == play_url)
        dl_res = await db_session.execute(dl_stmt)
        cached_dl = dl_res.scalar_one_or_none()
        
        qualities = {}
        db_cache_id = None
        
        if cached_dl and (datetime.now(timezone.utc) - cached_dl.created_at) < timedelta(hours=CACHE_EXPIRATION_HOURS):
            logger.info(f"Download links cache hit for play URL: {play_url}")
            qualities = cached_dl.qualities
            db_cache_id = cached_dl.id
        else:
            logger.info(f"Download links cache miss/expired for play URL: {play_url}. Scraping links...")
            await status_msg.edit_text("🔄 Resolving direct download links for the episode...")
            scraped_links = await get_download_links_scraper(play_url)
            
            if not scraped_links:
                logger.error(f"Failed to scrape download links from play page: {play_url}")
                await status_msg.edit_text("❌ Failed to parse download links for this episode. Try again later.")
                await state.clear()
                return
                
            qualities = scraped_links
            
            # Cache resolved download links
            if cached_dl:
                logger.info(f"Updating expired download cache for play URL: {play_url}")
                cached_dl.qualities = qualities
                cached_dl.created_at = datetime.now(timezone.utc)
                db_session.add(cached_dl)
                await db_session.commit()
                db_cache_id = cached_dl.id
            else:
                logger.info(f"Creating new download cache entry for play URL: {play_url}")
                new_dl = DownloadCache(
                    play_url=play_url,
                    qualities=qualities
                )
                db_session.add(new_dl)
                await db_session.commit()
                db_cache_id = new_dl.id
                
        # Prompt user to choose video quality
        keyboard_buttons = [
            [InlineKeyboardButton(text="⭐ Auto (Smart Size <= 2GB)", callback_data=f"dl:auto:{db_cache_id}")]
        ]
        
        quality_row = []
        for q in ["1080p", "720p", "480p", "360p"]:
            if q in qualities:
                quality_row.append(InlineKeyboardButton(text=q, callback_data=f"dl:{q}:{db_cache_id}"))
        if quality_row:
            keyboard_buttons.append(quality_row)
            
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await status_msg.delete()
        await message.answer(
            f"🎬 **Anime**: {anime_title}\n"
            f"🔢 **Episode**: {matched_ep['ep_number']}\n\n"
            f"Choose your download quality below:",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        
        # Clean up conversation state
        await state.clear()
        
    except Exception:
        logger.exception("Error in process while processing episode selection")
        await status_msg.edit_text("❌ Error processing download. Please try again.")
        await state.clear()

@router.callback_query(F.data.startswith("dl:"))
async def handle_download_callback(callback: CallbackQuery, db_session: AsyncSession):
    """
    Triggers download from selected quality or runs smart quality fallbacks.
    """
    parts = callback.data.split(":")
    requested_quality = parts[1]
    cache_id = int(parts[2])
    
    # Retrieve download cache
    stmt = select(DownloadCache).where(DownloadCache.id == cache_id)
    res = await db_session.execute(stmt)
    dl_cache = res.scalar_one_or_none()
    
    if not dl_cache:
        logger.warning(f"Download cache entry not found or expired (ID: {cache_id})")
        await callback.answer("❌ Episode download link expired. Please search again.", show_alert=True)
        return
        
    await callback.answer()
    
    # Delete original menu message to avoid spamming the UI
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    logger.info(f"Quality selected: '{requested_quality}' (Download Cache ID: {cache_id}, User ID: {callback.from_user.id})")
    await process_and_send_video(
        bot=callback.bot,
        message=callback.message,
        qualities=dl_cache.qualities,
        requested_quality=requested_quality
    )
