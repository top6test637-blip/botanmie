from datetime import datetime, timedelta, timezone
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram.filters import StateFilter
from app.database.models import SearchCache, UserFavorites
from app.services.anilist import search_anilist
from app.services.scraper import search_anime_scraper
from app.utils.logging_config import logger

router = Router(name="search")

class SearchStates(StatesGroup):
    waiting_for_episode = State()

CACHE_EXPIRATION_HOURS = 24

@router.message(F.text & ~F.text.startswith("/"), StateFilter(None))
async def handle_anime_search(message: Message, db_session: AsyncSession, state: FSMContext):
    """
    Handles search queries. Queries database cache first,
    then normalizes using AniList GraphQL API and displays matches.
    """
    query = message.text.strip().lower()
    if not query:
        return

    logger.info(f"Starting search for anime: '{query}' (User ID: {message.from_user.id})")

    # Check search cache first
    stmt = select(SearchCache).where(SearchCache.query_text == query)
    res = await db_session.execute(stmt)
    cached = res.scalar_one_or_none()

    resolved_anime = []

    # If cached and not expired (24h)
    if cached and (datetime.now(timezone.utc) - cached.created_at) < timedelta(hours=CACHE_EXPIRATION_HOURS):
        logger.info(f"Cache hit for search query: '{query}' (AniList ID: {cached.anilist_id})")
        resolved_anime.append({
            "anilist_id": cached.anilist_id,
            "title_english": cached.title_english,
            "title_romaji": cached.title_romaji,
            "description": cached.description,
            "image_url": cached.image_url
        })
    else:
        logger.info(f"Cache miss or expired for search query: '{query}'. Resolving via AniList GraphQL API...")
        # Resolve via AniList GraphQL
        status_msg = await message.answer("🔍 Normalizing query using AniList...")
        try:
            anilist_results = await search_anilist(query)
            await status_msg.delete()
            
            if not anilist_results:
                logger.info(f"AniList returned 0 results for query: '{query}'")
                await message.answer("❌ No matching anime found on AniList. Try double-checking your query.")
                return
                
            resolved_anime = anilist_results
            
            # Cache the top result
            top_result = anilist_results[0]
            if cached:
                logger.info(f"Updating expired cache entry for query: '{query}'")
                cached.anilist_id = top_result["anilist_id"]
                cached.title_english = top_result["title_english"]
                cached.title_romaji = top_result["title_romaji"]
                cached.description = top_result["description"]
                cached.image_url = top_result["image_url"]
                cached.created_at = datetime.now(timezone.utc)
            else:
                logger.info(f"Creating new cache entry for query: '{query}'")
                new_cache = SearchCache(
                    query_text=query,
                    anilist_id=top_result["anilist_id"],
                    title_english=top_result["title_english"],
                    title_romaji=top_result["title_romaji"],
                    description=top_result["description"],
                    image_url=top_result["image_url"]
                )
                db_session.add(new_cache)
            await db_session.commit()
            
        except Exception as e:
            logger.exception("Error in process during query normalization")
            try:
                await status_msg.delete()
            except Exception:
                pass
            await message.answer(f"❌ Error during query normalization: {e}")
            return

    # Build selection keyboard
    keyboard_buttons = []
    for anime in resolved_anime[:5]:
        title = anime["title_english"] or anime["title_romaji"]
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=title[:40] + "..." if len(title) > 43 else title,
                callback_data=f"sel_anime:{anime['anilist_id']}"
            )
        ])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await message.answer(
        "✨ **AniList Search Results**:\nSelect the anime to load episode selection:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("sel_anime:"))
async def handle_anime_selection(callback: CallbackQuery, db_session: AsyncSession, state: FSMContext):
    """
    Handles anime selection from the keyboard.
    Displays cover image/details and transitions to FSM state to prompt for episode.
    """
    anilist_id = int(callback.data.split(":")[1])
    logger.info(f"Anime selection triggered (AniList ID: {anilist_id}, User ID: {callback.from_user.id})")
    
    # Retrieve details from search_cache
    stmt = select(SearchCache).where(SearchCache.anilist_id == anilist_id)
    res = await db_session.execute(stmt)
    cache_entry = res.scalars().first()
    
    if not cache_entry:
        logger.warning(f"Anime cache entry not found for AniList ID: {anilist_id}")
        await callback.answer("❌ Anime cache details not found. Please search again.", show_alert=True)
        return
        
    title = cache_entry.title_english or cache_entry.title_romaji
    logger.info(f"Loaded anime details from cache: '{title}'")
    
    # Store anime details in FSM context
    await state.update_data(
        anilist_id=anilist_id,
        anime_title=title,
        title_romaji=cache_entry.title_romaji,
        title_english=cache_entry.title_english
    )
    
    # Transition to waiting for episode number
    await state.set_state(SearchStates.waiting_for_episode)
    await callback.answer()

    details_text = (
        f"🎬 **Selected Anime**: {title}\n"
        f"📝 Description: {cache_entry.description[:250] + '...' if cache_entry.description else 'None'}\n\n"
        f"🔢 **Please type the Episode Number you want to get** (e.g. `1`, `12`, `24`):"
    )
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Add to Favorites", callback_data=f"fav_add:{anilist_id}")]
    ])
    
    if cache_entry.image_url:
        await callback.message.answer_photo(
            photo=cache_entry.image_url,
            caption=details_text,
            reply_markup=markup,
            parse_mode="Markdown"
        )
    else:
        await callback.message.answer(
            details_text,
            reply_markup=markup,
            parse_mode="Markdown"
        )

@router.callback_query(F.data.startswith("fav_add:"))
async def handle_add_favorite(callback: CallbackQuery, db_session: AsyncSession):
    """
    Saves the anime to UserFavorites table in the database and provides confirmation.
    """
    anilist_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    logger.info(f"Add favorite triggered (AniList ID: {anilist_id}, User ID: {user_id})")

    # Retrieve title from search cache
    stmt = select(SearchCache).where(SearchCache.anilist_id == anilist_id)
    res = await db_session.execute(stmt)
    cache_entry = res.scalars().first()

    if not cache_entry:
        logger.warning(f"Cache entry not found during favorite addition for AniList ID: {anilist_id}")
        await callback.answer("❌ Anime details not found in cache. Search again.", show_alert=True)
        return

    title = cache_entry.title_english or cache_entry.title_romaji

    # Check if already in favorites
    fav_stmt = select(UserFavorites).where(
        (UserFavorites.user_id == user_id) & (UserFavorites.anilist_id == anilist_id)
    )
    fav_res = await db_session.execute(fav_stmt)
    existing_fav = fav_res.scalar_one_or_none()

    if existing_fav:
        logger.info(f"Anime '{title}' is already in favorites for User ID: {user_id}")
        await callback.answer(f"⭐ '{title}' is already in your favorites!", show_alert=False)
        return

    # Add to favorites
    try:
        new_fav = UserFavorites(
            user_id=user_id,
            anilist_id=anilist_id,
            anime_title=title
        )
        db_session.add(new_fav)
        await db_session.commit()
        
        logger.info(f"Successfully added '{title}' (AniList ID: {anilist_id}) to favorites for User ID: {user_id}")
        await callback.answer(f"✅ Added '{title}' to Favorites!", show_alert=False)
    except Exception as e:
        logger.exception("Error in process while adding favorite")
        await db_session.rollback()
        await callback.answer(f"❌ Failed to save: {e}", show_alert=True)
