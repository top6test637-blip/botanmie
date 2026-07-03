from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

router = Router(name="start")

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handles the /start command."""
    welcome_text = (
        "👋 **مرحباً بك في بوت البحث وتحميل الأنمي المتقدم!**\n\n"
        "يقوم هذا البوت بتنظيم عمليات البحث باستخدام **AniList GraphQL**، والبحث عن روابط البث المتاحة، "
        "وإرسال ملفات الفيديو إليك مباشرة. كما أنه يطبق **ذكاء حجم الملف** لتقليل جودة الفيديو تلقائياً "
        "إذا تجاوز الملف حد حجم تلغرام البالغ 2 جيجابايت.\n\n"
        "🔍 **طريقة الاستخدام**:\n"
        "أرسل اسم الأنمي الذي تريد البحث عنه (مثال: `Luffy` أو `One Piece` أو أسماء باللغة العربية).\n\n"
        "اكتب /help في أي وقت لعرض تعليمات البوت."
    )
    await message.answer(welcome_text, parse_mode="Markdown")

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handles the /help command."""
    help_text = (
        "ℹ️ **تعليمات البوت**:\n\n"
        "1. **البحث**: أرسل اسم الأنمي. يقوم البوت بحل أسماء الشخصيات والأخطاء الإملائية إلى العناوين الرسمية.\n"
        "2. **الاختيار**: اختر الأنمي المطلوب من قائمة نتائج البحث.\n"
        "3. **رقم الحلقة**: اكتب رقم الحلقة المطلوبة عندما يطلب منك البوت ذلك.\n"
        "4. **جودة التحميل**: اختر الجودة المطلوبة، أو اختر **تلقائي (حجم ذكي)** لجعل البوت يختار أعلى جودة مناسبة تحت 2 جيجابايت.\n\n"
        "⚙️ *ملاحظة: تقتصر حدود رفع البوتات القياسية في تلغرام على 50 ميجابايت. يتميز هذا البوت بدعم الرفع حتى 2 جيجابايت عند تشغيله مع خادم Bot API محلي.*"
    )
    await message.answer(help_text, parse_mode="Markdown")
