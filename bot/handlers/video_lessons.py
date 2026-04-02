from telegram import Update
from telegram.ext import ContextTypes
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from bot.database.db import get_user_lang
from bot.services.i18n import get_trans

# ─── Video Lessons Data (24 lessons, 8 categories) ────────────────────────
VIDEO_LESSONS = [
    # Alphabet & Pronunciation (A1)
    {
        "id": "alpha-1",
        "title": "English Alphabet Pronunciation Guide",
        "title_uz": "Ingliz tilidagi alifbo va talaffuz qo'llanmasi",
        "youtube_id": "zFmG7YJXOKE",
        "level": "A1",
        "category": "Alphabet & Pronunciation",
        "category_uz": "Alifbo va talaffuz",
        "duration": "18:24",
        "description": "Learn the correct pronunciation of all 26 English letters, including vowel and consonant sounds.",
        "description_uz": "Ingliz tilidagi barcha 26 harfning to'g'ri talaffuzini o'rganing.",
    },
    {
        "id": "alpha-2",
        "title": "English Vowel Sounds Masterclass",
        "title_uz": "Ingliz tilida unli tovushlar mukammal darsi",
        "youtube_id": "LmGPj5T2Phk",
        "level": "A1",
        "category": "Alphabet & Pronunciation",
        "category_uz": "Alifbo va talaffuz",
        "duration": "22:15",
        "description": "Master all English vowel sounds including short vowels, long vowels, and diphthongs.",
        "description_uz": "Barcha ingliz unli tovushlarini — qisqa, cho'ziq va diftonglarni mukammal o'rganing.",
    },
    {
        "id": "alpha-3",
        "title": "Common English Pronunciation Mistakes",
        "title_uz": "Ingliz tilida tez-tez uchraydigan talaffuz xatoliklari",
        "youtube_id": "oRYQp7j9XsA",
        "level": "A1",
        "category": "Alphabet & Pronunciation",
        "category_uz": "Alifbo va talaffuz",
        "duration": "16:42",
        "description": "Discover and fix the most common pronunciation mistakes that English learners make.",
        "description_uz": "Ingliz tili o'rganuvchilar qiladigan eng ko'p talaffuz xatolarini toping va tuzating.",
    },
    # Basic Grammar (A1-A2)
    {
        "id": "gram-1",
        "title": "Present Simple Tense Explained",
        "title_uz": "Hozirgi oddiy zamon tushuntirilgan",
        "youtube_id": "oXgAYeG1lnQ",
        "level": "A1",
        "category": "Basic Grammar",
        "category_uz": "Asosiy grammatika",
        "duration": "20:33",
        "description": "Learn how to form and use the Present Simple tense for daily routines, facts, and habits.",
        "description_uz": "Kundalik ishlar, faktlar va odatlar uchun Hozirgi oddiy zamondan foydalanishni o'rganing.",
    },
    {
        "id": "gram-2",
        "title": "Past Simple vs Present Perfect",
        "title_uz": "O'tgan oddiy zamon va hozirgi tugallangan zamon farqi",
        "youtube_id": "gyBGt1nKDJY",
        "level": "A2",
        "category": "Basic Grammar",
        "category_uz": "Asosiy grammatika",
        "duration": "25:10",
        "description": "Understand the key differences between Past Simple and Present Perfect tenses.",
        "description_uz": "O'tgan oddiy zamon va hozirgi tugallangan zamon o'rtasidagi asosiy farqlarni tushuning.",
    },
    {
        "id": "gram-3",
        "title": "Articles: A, An, The - Complete Guide",
        "title_uz": "Artikllar: A, An, The — to'liq qo'llanma",
        "youtube_id": "W1q1D7-jBiI",
        "level": "A2",
        "category": "Basic Grammar",
        "category_uz": "Asosiy grammatika",
        "duration": "19:55",
        "description": "Master the use of English articles (a, an, the) with easy-to-follow rules and exceptions.",
        "description_uz": "Ingliz artikllaridan (a, an, the) foydalanishni qoidalar va istisnolar bilan o'rganing.",
    },
    # Everyday English (A2)
    {
        "id": "every-1",
        "title": "50 Most Common English Phrases",
        "title_uz": "Eng ko'p ishlatiladigan 50 ingliz iborasi",
        "youtube_id": "mHNR5zfJC9Y",
        "level": "A2",
        "category": "Everyday English",
        "category_uz": "Kundalik ingliz tili",
        "duration": "24:08",
        "description": "Learn the 50 most frequently used English phrases in daily conversations.",
        "description_uz": "Kundalik suhbatlarda eng ko'p ishlatiladigan 50 ingliz iborasini o'rganing.",
    },
    {
        "id": "every-2",
        "title": "How to Order Food in English",
        "title_uz": "Ingliz tilida ovqat buyurtma berish",
        "youtube_id": "pMfiRmPNt7s",
        "level": "A2",
        "category": "Everyday English",
        "category_uz": "Kundalik ingliz tili",
        "duration": "15:37",
        "description": "Learn essential phrases for ordering food at restaurants and cafes.",
        "description_uz": "Restoran va kafelarda ovqat buyurtma berish uchun muhim iboralarni o'rganing.",
    },
    {
        "id": "every-3",
        "title": "English for Shopping and Bargaining",
        "title_uz": "Sotib olish va narx kelishish uchun ingliz tili",
        "youtube_id": "KdKx6SBbMOE",
        "level": "A2",
        "category": "Everyday English",
        "category_uz": "Kundalik ingliz tili",
        "duration": "17:22",
        "description": "Master shopping vocabulary and phrases for asking prices and bargaining.",
        "description_uz": "Narxlarni so'rash va narx kelishish uchun savdo lug'ati va iboralarni o'rganing.",
    },
    # Intermediate Grammar (B1)
    {
        "id": "int-gram-1",
        "title": "Conditionals: If Clauses Explained",
        "title_uz": "Shart jumlalari: Agar gaplari tushuntirilgan",
        "youtube_id": "6X8eCRkBmrM",
        "level": "B1",
        "category": "Intermediate Grammar",
        "category_uz": "O'rta grammatika",
        "duration": "28:45",
        "description": "Learn all four types of conditional sentences with clear rules and examples.",
        "description_uz": "Barcha to'rt xil shart jumla turlarini qoidalar va misollar bilan o'rganing.",
    },
    {
        "id": "int-gram-2",
        "title": "Passive Voice Made Easy",
        "title_uz": "O'tgan zamon osonlashtirilgan",
        "youtube_id": "e50mvTgSsWk",
        "level": "B1",
        "category": "Intermediate Grammar",
        "category_uz": "O'rta grammatika",
        "duration": "21:16",
        "description": "Understand how to form and use passive voice in all tenses.",
        "description_uz": "Barcha zamonlarda nisbat o'tgan shaklida gapirishni o'rganing.",
    },
    {
        "id": "int-gram-3",
        "title": "Reported Speech: Direct to Indirect",
        "title_uz": "Bilvosita nutq: To'g'ridan-to'g'ridan bilvosita nutqqa",
        "youtube_id": "beKqaGBGObc",
        "level": "B1",
        "category": "Intermediate Grammar",
        "category_uz": "O'rta grammatika",
        "duration": "23:30",
        "description": "Learn how to convert direct speech into reported speech.",
        "description_uz": "To'g'ridan-to'g'ri nutqni bilvosita nutqqa aylantirishni o'rganing.",
    },
    # Business English (B1-B2)
    {
        "id": "biz-1",
        "title": "Business English: Writing Professional Emails",
        "title_uz": "Biznes ingliz tili: Professional xatlar yozish",
        "youtube_id": "m2SxawUHPDQ",
        "level": "B1",
        "category": "Business English",
        "category_uz": "Biznes ingliz tili",
        "duration": "20:44",
        "description": "Learn how to write professional emails for the workplace.",
        "description_uz": "Ish joyi uchun professional xatlar yozishni o'rganing.",
    },
    {
        "id": "biz-2",
        "title": "English for Job Interviews",
        "title_uz": "Ish intervyusi uchun ingliz tili",
        "youtube_id": "LpP_cG4jToE",
        "level": "B2",
        "category": "Business English",
        "category_uz": "Biznes ingliz tili",
        "duration": "26:18",
        "description": "Master common interview questions and learn how to answer them confidently.",
        "description_uz": "Eng ko'p beriladigan intervyu savollari va ularni ishonchli javob berishni o'rganing.",
    },
    {
        "id": "biz-3",
        "title": "Business Meetings: Key Vocabulary & Phrases",
        "title_uz": "Biznes uchrashuvlari: Asosiy lug'at va iboralar",
        "youtube_id": "K8MxGfQ1xHk",
        "level": "B2",
        "category": "Business English",
        "category_uz": "Biznes ingliz tili",
        "duration": "19:52",
        "description": "Essential vocabulary and phrases for participating in and leading business meetings.",
        "description_uz": "Biznes uchrashuvlarida ishtirok etish va boshqarish uchun kerakli lug'at va iboralarni o'rganing.",
    },
    # Advanced Speaking (B2-C1)
    {
        "id": "adv-speak-1",
        "title": "How to Sound More Natural in English",
        "title_uz": "Ingliz tilida tabiiyroq gapirish usullari",
        "youtube_id": "Ge6rg_cM0GQ",
        "level": "B2",
        "category": "Advanced Speaking",
        "category_uz": "Kengaytiril gapirish",
        "duration": "22:06",
        "description": "Learn connected speech, reductions, and natural intonation patterns.",
        "description_uz": "Bog'langan nutq, qisqartmalar va tabiiy ohang naqshlarini o'rganing.",
    },
    {
        "id": "adv-speak-2",
        "title": "Advanced English Conversation Skills",
        "title_uz": "Kengaytirilgan ingliz suhbat ko'nikmalari",
        "youtube_id": "SHOGWg7wU6E",
        "level": "C1",
        "category": "Advanced Speaking",
        "category_uz": "Kengaytiril gapirish",
        "duration": "27:33",
        "description": "Develop advanced conversation skills including turn-taking and expressing complex opinions.",
        "description_uz": "Suhbatni boshqarish va murakkab fikrlarni ravon ifoda etish ko'nikmalarini rivojlantiring.",
    },
    {
        "id": "adv-speak-3",
        "title": "English Debate & Argumentation",
        "title_uz": "Ingliz tilida munozara va bahs",
        "youtube_id": "T4gSD0hfXPI",
        "level": "C1",
        "category": "Advanced Speaking",
        "category_uz": "Kengaytiril gapirish",
        "duration": "24:17",
        "description": "Learn to express and defend opinions and participate in formal debates.",
        "description_uz": "Fikrlarni ifoda etish va ingliz tilida rasmiy munozaralarda ishtirok etishni o'rganing.",
    },
    # IELTS Preparation (B2-C1)
    {
        "id": "ielts-1",
        "title": "IELTS Speaking: Band 7+ Tips",
        "title_uz": "IELTS gapirish: 7+ ball uchun maslahatlar",
        "youtube_id": "5i0Hzq4xGGs",
        "level": "B2",
        "category": "IELTS Preparation",
        "category_uz": "IELTS tayyorgarlik",
        "duration": "30:11",
        "description": "Expert tips and strategies for achieving a Band 7 or higher in the IELTS Speaking test.",
        "description_uz": "IELTS gapirish imtihonida 7 yoki undan yuqori ball olish uchun ekspert maslahatlari.",
    },
    {
        "id": "ielts-2",
        "title": "IELTS Writing Task 2: Essay Structure",
        "title_uz": "IELTS yozish 2-topshiriq: Insho tuzilmasi",
        "youtube_id": "JDIcVWKj7QM",
        "level": "C1",
        "category": "IELTS Preparation",
        "category_uz": "IELTS tayyorgarlik",
        "duration": "28:45",
        "description": "Master the essay structure for IELTS Writing Task 2.",
        "description_uz": "IELTS yozish 2-topshiriq uchun insho tuzilmasini mukammal o'rganing.",
    },
    {
        "id": "ielts-3",
        "title": "IELTS Listening: Top Strategies",
        "title_uz": "IELTS tinglash: Eng yaxshi strategiyalar",
        "youtube_id": "mWYJgGxK0Jc",
        "level": "C1",
        "category": "IELTS Preparation",
        "category_uz": "IELTS tayyorgarlik",
        "duration": "25:39",
        "description": "Proven strategies for the IELTS Listening test including map labeling and multiple choice.",
        "description_uz": "IELTS tinglash imtihoni uchun isbotlangan strategiyalar.",
    },
    # English Slang & Idioms (B2)
    {
        "id": "slang-1",
        "title": "30 Essential English Idioms",
        "title_uz": "30 ta muhim ingliz iboralari (idiomlar)",
        "youtube_id": "pK_k2RQyJZo",
        "level": "B2",
        "category": "English Slang & Idioms",
        "category_uz": "Ingliz slangi va iboralar",
        "duration": "19:28",
        "description": "Learn 30 of the most commonly used English idioms with clear explanations.",
        "description_uz": "Eng ko'p ishlatiladigan 30 ta ingliz idiomasini tushuntirishlar bilan o'rganing.",
    },
    {
        "id": "slang-2",
        "title": "American English Slang Words You Need",
        "title_uz": "Sizga kerak bo'lgan amerika inglizcha atamalar",
        "youtube_id": "pQ3_OlfgjQQ",
        "level": "B2",
        "category": "English Slang & Idioms",
        "category_uz": "Ingliz slangi va iboralar",
        "duration": "17:53",
        "description": "Discover popular American slang words used in daily conversations and social media.",
        "description_uz": "Kundalik suhbatlar va ijtimoiy tarmoqlarda ishlatiladigan mashhur amerika atamalarini o'rganing.",
    },
    {
        "id": "slang-3",
        "title": "British vs American English Differences",
        "title_uz": "Britaniya va Amerika ingliz tili farqlari",
        "youtube_id": "1Of8H_qHG2E",
        "level": "B2",
        "category": "English Slang & Idioms",
        "category_uz": "Ingliz slangi va iboralar",
        "duration": "21:07",
        "description": "Explore key differences between British and American English vocabulary and pronunciation.",
        "description_uz": "Britaniya va Amerika ingliz tili o'rtasidagi asosiy farqlarni o'rganing.",
    },
]

# Category metadata with emoji
VIDEO_CATEGORIES = [
    ("Alphabet & Pronunciation", "Alifbo va talaffuz", "🔤"),
    ("Basic Grammar", "Asosiy grammatika", "📐"),
    ("Everyday English", "Kundalik ingliz tili", "💬"),
    ("Intermediate Grammar", "O'rta grammatika", "📐"),
    ("Business English", "Biznes ingliz tili", "💼"),
    ("Advanced Speaking", "Kengaytiril gapirish", "🎯"),
    ("IELTS Preparation", "IELTS tayyorgarlik", "📝"),
    ("English Slang & Idioms", "Ingliz slangi va iboralar", "🗣️"),
]


def _get_category_title(cat_en: str, cat_uz: str, lang: str) -> str:
    return cat_uz if lang == "uz" else cat_en


def _get_lesson_title(lesson: dict, lang: str) -> str:
    return lesson.get("title_uz", lesson["title"]) if lang == "uz" else lesson["title"]


def _get_lesson_desc(lesson: dict, lang: str) -> str:
    return lesson.get("description_uz", lesson["description"]) if lang == "uz" else lesson["description"]


# ─── 1. Video Lessons Menu ────────────────────────────────────────────────
async def handle_video_lessons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show video lesson category selection."""
    user_id = update.effective_user.id
    lang = await get_user_lang(user_id)
    t = lambda k, **kw: get_trans(lang, k, **kw)

    keyboard = []
    for cat_en, cat_uz, emoji in VIDEO_CATEGORIES:
        title = _get_category_title(cat_en, cat_uz, lang)
        # Count lessons in category
        count = len([v for v in VIDEO_LESSONS if v["category"] == cat_en])
        keyboard.append([InlineKeyboardButton(
            f"{emoji} {title} ({count})",
            callback_data=f"vidcat_{cat_en}"
        )])

    back_btn = InlineKeyboardButton(f"◀️ {t('btn_main_menu')}", callback_data="vid_back")
    keyboard.append([back_btn])

    msg = (
        f"🎬 *{t('videos_title')}*\n\n"
        f"{t('videos_select_category')}:\n"
        f"📊 {t('videos_total')}: *{len(VIDEO_LESSONS)}*"
    )
    await update.message.reply_text(
        msg, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ─── 2. Video Category ─────────────────────────────────────────────────────
async def handle_video_category(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                  category: str) -> None:
    """Show videos in a category."""
    user_id = update.effective_user.id
    lang = await get_user_lang(user_id)
    t = lambda k, **kw: get_trans(lang, k, **kw)

    # Find category metadata
    cat_meta = None
    for cat_en, cat_uz, emoji in VIDEO_CATEGORIES:
        if cat_en == category:
            cat_meta = (cat_en, cat_uz, emoji)
            break

    if not cat_meta:
        await update.callback_query.message.reply_text("❌ Category not found.")
        return

    cat_en, cat_uz, emoji = cat_meta
    cat_title = _get_category_title(cat_en, cat_uz, lang)
    lessons = [v for v in VIDEO_LESSONS if v["category"] == cat_en]

    keyboard = []
    for lesson in lessons:
        title = _get_lesson_title(lesson, lang)
        keyboard.append([InlineKeyboardButton(
            f"▶️ {title} ({lesson['duration']})",
            callback_data=f"vidplay_{lesson['id']}"
        )])

    back_btn = InlineKeyboardButton(f"◀️ {t('videos_back')}", callback_data="vid_menu")
    keyboard.append([back_btn])

    msg = (
        f"{emoji} *{cat_title}*\n\n"
        f"{t('videos_select_lesson')} ({len(lessons)}):"
    )
    await update.callback_query.message.reply_text(
        msg, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ─── 3. Video Player ───────────────────────────────────────────────────────
async def handle_video_play(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              lesson_id: str) -> None:
    """Show video lesson with YouTube link and description."""
    user_id = update.effective_user.id
    lang = await get_user_lang(user_id)
    t = lambda k, **kw: get_trans(lang, k, **kw)

    lesson = None
    for v in VIDEO_LESSONS:
        if v["id"] == lesson_id:
            lesson = v
            break

    if not lesson:
        await update.callback_query.message.reply_text("❌ Lesson not found.")
        return

    title = _get_lesson_title(lesson, lang)
    desc = _get_lesson_desc(lesson, lang)
    youtube_url = f"https://www.youtube.com/watch?v={lesson['youtube_id']}"

    # Find category for back button
    back_data = f"vidcat_{lesson['category']}"

    keyboard = [
        [InlineKeyboardButton(
            f"▶️ {t('videos_watch_yt')}",
            url=youtube_url
        )],
        [InlineKeyboardButton(f"◀️ {t('videos_back_cat')}", callback_data=back_data)],
        [InlineKeyboardButton(f"◀️ {t('btn_main_menu')}", callback_data="vid_back")],
    ]

    msg = (
        f"🎬 *{title}*\n"
        f"⏱ {lesson['duration']} | 📊 {lesson['level']}\n\n"
        f"📝 {desc}\n\n"
        f"🔗 [YouTube]({youtube_url})"
    )
    await update.callback_query.message.reply_text(
        msg, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )


# ─── 4. Video Callback Router ──────────────────────────────────────────────
async def handle_video_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route all video-related callbacks."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "vid_back":
        return  # Let main callback handle it

    if data == "vid_menu":
        from bot.handlers.video_lessons import handle_video_lessons
        class FakeUpdate:
            def __init__(self, orig, msg):
                self.effective_user = orig.from_user
                self.effective_chat = msg.chat
                self.message = msg
        fake = FakeUpdate(query, query.message)
        await handle_video_lessons(fake, context)
        return

    if data.startswith("vidcat_"):
        category = data.replace("vidcat_", "")
        await handle_video_category(update, context, category)
        return

    if data.startswith("vidplay_"):
        lesson_id = data.replace("vidplay_", "")
        await handle_video_play(update, context, lesson_id)
        return
