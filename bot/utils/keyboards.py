from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from bot.services.i18n import get_trans, TRANSLATIONS

# ─── 30 supported languages (shown in native script) ─────────────────────────
LANGUAGES_30 = [
    ("🇯🇵 日本語 (Japanese)",    "ja"),
    ("🇰🇷 한국어 (Korean)",      "ko"),
    ("🇨🇳 中文 (Chinese)",       "zh-CN"),
    ("🇸🇦 العربية (Arabic)",     "ar"),
    ("🇮🇳 हिन्दी (Hindi)",       "hi"),
    ("🇹🇷 Türkçe (Turkish)",     "tr"),
    ("🇮🇷 فارسی (Persian)",      "fa"),
    ("🇹🇭 ไทย (Thai)",           "th"),
    ("🇻🇳 Tiếng Việt (Vietnamese)", "vi"),
    ("🇮🇩 Bahasa Indonesia",     "id"),
    ("🇲🇾 Bahasa Melayu",        "ms"),
    ("🇧🇩 বাংলা (Bengali)",      "bn"),
    ("🇵🇰 اردو (Urdu)",          "ur"),
    ("🇱🇰 தமிழ் (Tamil)",        "ta"),
    ("🇳🇵 नेपाली (Nepali)",      "ne"),
    ("🇰🇿 Қазақша (Kazakh)",     "kk"),
    ("🇷🇺 Русский (Russian)",    "ru"),
    ("🇩🇪 Deutsch (German)",      "de"),
    ("🇫🇷 Français (French)",     "fr"),
    ("🇪🇸 Español (Spanish)",     "es"),
    ("🇮🇹 Italiano (Italian)",    "it"),
    ("🇵🇹 Português (Portuguese)","pt"),
    ("🇳🇱 Nederlands (Dutch)",    "nl"),
    ("🇵🇱 Polski (Polish)",       "pl"),
    ("🇺🇦 Українська (Ukrainian)","uk"),
    ("🇬🇷 Ελληνικά (Greek)",      "el"),
    ("🇮🇱 עברית (Hebrew)",        "he"),
    ("🇨🇿 Čeština (Czech)",       "cs"),
    ("🇬🇧 English",               "en"),
    ("🇺🇿 O'zbekcha",             "uz"),
]

LANG_INFO = {code: name for name, code in LANGUAGES_30}


def get_main_menu(lang: str = "uz") -> ReplyKeyboardMarkup:
    t = lambda k: get_trans(lang, k)
    keyboard = [
        [KeyboardButton(t("btn_translator")),   KeyboardButton(t("btn_other_lang"))],
        [KeyboardButton(t("btn_voice")),         KeyboardButton(t("btn_photo"))],
        [KeyboardButton(t("btn_file")),          KeyboardButton(t("btn_grammar"))],
        [KeyboardButton(t("btn_tenses")),        KeyboardButton(t("btn_tests"))],
        [KeyboardButton(t("btn_videos")),        KeyboardButton(t("btn_games"))],
        [KeyboardButton(t("btn_vocabulary")),    KeyboardButton(t("btn_ai"))],
        [KeyboardButton(t("btn_roleplay")),      KeyboardButton(t("btn_history"))],
        [KeyboardButton(t("btn_status")),        KeyboardButton(t("btn_settings"))],
        [KeyboardButton(t("btn_about"))],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_language_selection_keyboard() -> InlineKeyboardMarkup:
    """30-language selection as inline keyboard for /start."""
    keyboard = []
    for i in range(0, len(LANGUAGES_30), 3):
        row = []
        for j in range(3):
            if i + j < len(LANGUAGES_30):
                name, code = LANGUAGES_30[i + j]
                row.append(InlineKeyboardButton(name, callback_data=f"setlang_{code}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def get_audio_button(context_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔊 Audio",     callback_data=f"audio_{context_id}"),
        InlineKeyboardButton("💾 Save Word", callback_data=f"save_{context_id}"),
    ]])


def get_history_buttons(context_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔊 Audio",  callback_data=f"audio_{context_id}"),
        InlineKeyboardButton("💾 Save",   callback_data=f"save_{context_id}"),
        InlineKeyboardButton("🗑 Delete", callback_data=f"del_{context_id}"),
    ]])


def get_other_languages_buttons() -> InlineKeyboardMarkup:
    keyboard = []
    for i in range(0, len(LANGUAGES_30), 2):
        row = [InlineKeyboardButton(LANGUAGES_30[i][0], callback_data=f"lang_{LANGUAGES_30[i][1]}")]
        if i + 1 < len(LANGUAGES_30):
            row.append(InlineKeyboardButton(LANGUAGES_30[i+1][0], callback_data=f"lang_{LANGUAGES_30[i+1][1]}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def get_tenses_menu(lang: str = "uz") -> ReplyKeyboardMarkup:
    topics = [
        "⏰ Present Simple",    "🔄 Present Continuous",
        "✅ Present Perfect",   "🔁 Pres. Perfect Cont.",
        "🕰️ Past Simple",       "🔄 Past Continuous",
        "✔️ Past Perfect",      "🔁 Past Perfect Cont.",
        "🔮 Future Simple",     "📅 Be Going To",
        "🔄 Future Continuous", "✅ Future Perfect",
    ]
    keyboard = []
    for i in range(0, len(topics), 2):
        row = [KeyboardButton(topics[i])]
        if i + 1 < len(topics):
            row.append(KeyboardButton(topics[i+1]))
        keyboard.append(row)
    keyboard.append([KeyboardButton(get_trans(lang, "btn_main_menu"))])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_tenses_nav_buttons(tense_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    learned_text = get_trans(lang, "btn_learned")
    buttons = []
    if tense_id > 1:
        buttons.append(InlineKeyboardButton("◀️ Oldingi", callback_data=f"tense_{tense_id - 1}"))
    buttons.append(InlineKeyboardButton("📝 Quiz", callback_data=f"quiz_tense_{tense_id}"))
    if tense_id < 12:
        buttons.append(InlineKeyboardButton("▶️ Keyingi", callback_data=f"tense_{tense_id + 1}"))
    row2 = [InlineKeyboardButton(f"{learned_text} (Bu mavzu)", callback_data=f"learned_tense_{tense_id}")]
    return InlineKeyboardMarkup([buttons, row2])


def get_grammar_topics_menu(topics: list, lang: str = "uz") -> ReplyKeyboardMarkup:
    keyboard = []
    for i in range(0, len(topics), 2):
        row = [KeyboardButton(topics[i])]
        if i + 1 < len(topics):
            row.append(KeyboardButton(topics[i+1]))
        keyboard.append(row)
    keyboard.append([KeyboardButton(get_trans(lang, "btn_main_menu"))])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_grammar_action_buttons(topic_id: str, lang: str = "uz") -> InlineKeyboardMarkup:
    learned_text = get_trans(lang, "btn_learned")
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📝 Quiz",   callback_data=f"quiz_grammar_{topic_id}"),
            InlineKeyboardButton("🤖 Ask AI", callback_data=f"ask_ai_{topic_id}"),
        ],
        [InlineKeyboardButton(f"{learned_text} ✅", callback_data=f"learned_grammar_{topic_id}")]
    ])


def get_settings_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    t = lambda k: get_trans(lang, k)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_change_lang"), callback_data="settings_lang")],
        [InlineKeyboardButton("✏️ Ismni o'zgartirish / Change Name", callback_data="settings_name")],
        [InlineKeyboardButton(t("btn_change_nick"), callback_data="settings_nick")],
        [InlineKeyboardButton(t("btn_reset"),       callback_data="settings_reset")],
    ])


def get_status_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    t = lambda k: get_trans(lang, k)
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t("learned_topics_title"), callback_data="status_learned"),
            InlineKeyboardButton(t("pending_topics_title"), callback_data="status_pending"),
        ]
    ])


def get_quiz_topic_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Test topic selection keyboard."""
    topics = [
        "Present Simple", "Present Continuous", "Present Perfect",
        "Past Simple", "Past Continuous", "Past Perfect",
        "Future Simple", "Modal Verbs", "Conditionals",
        "Passive Voice", "Articles", "Prepositions",
        "Phrasal Verbs", "Idioms", "General Grammar",
    ]
    keyboard = []
    for i in range(0, len(topics), 2):
        row = [InlineKeyboardButton(topics[i], callback_data=f"qtopic_{topics[i]}")]
        if i + 1 < len(topics):
            row.append(InlineKeyboardButton(topics[i+1], callback_data=f"qtopic_{topics[i+1]}"))
        keyboard.append(row)
    # "Other" button
    other_label = "✏️ " + get_trans(lang, "other_topic").replace("📝 ", "")
    keyboard.append([InlineKeyboardButton("✏️ Other (Custom)", callback_data="qtopic_OTHER")])
    return InlineKeyboardMarkup(keyboard)


def get_quiz_count_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Test count selection: 5, 10, 15, 20, 30."""
    counts = [5, 10, 15, 20, 30]
    row = [InlineKeyboardButton(str(c), callback_data=f"qcount_{c}") for c in counts]
    return InlineKeyboardMarkup([row])


def get_roleplay_menu(lang: str = "uz") -> ReplyKeyboardMarkup:
    scenarios = [
        "🏨 Hotel check-in",         "✈️ Airport boarding gate",
        "🛒 Shopping at a store",    "🏥 Doctor's appointment",
        "🍽️ Restaurant ordering",    "💼 Job interview",
        "📞 Phone conversation",     "🚕 Taxi — directions",
        "🏦 At the bank",            "🎓 University enrollment",
        "🏫 Classroom situation",    "🚂 At the train station",
        "🛂 At customs / border",    "💊 At the pharmacy",
        "📮 At the post office",     "🏋️ At the gym",
    ]
    keyboard = []
    for i in range(0, len(scenarios), 2):
        row = [KeyboardButton(scenarios[i])]
        if i + 1 < len(scenarios):
            row.append(KeyboardButton(scenarios[i+1]))
        keyboard.append(row)
    keyboard.append([KeyboardButton(get_trans(lang, "btn_main_menu"))])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
