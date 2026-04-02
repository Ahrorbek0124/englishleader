import io
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from bot.services.translator_service import translate_text, detect_language
from bot.services.tts_service import process_text_to_speech
from bot.utils.keyboards import (
    get_audio_button, get_main_menu, get_roleplay_menu,
    get_other_languages_buttons, get_settings_keyboard, LANG_INFO
)
from bot.database.db import get_db_connection, get_user_lang
from bot.handlers.grammar import GRAMMAR_DATA, handle_grammar_selection
from bot.handlers.tenses import TENSE_MAPPING, handle_tense_selection
from bot.services.i18n import get_trans, get_button_key

GTTS_LANG_MAP = {
    "zh-CN": "zh-CN", "zh": "zh-CN",
    "he": "iw",
    "kk": "ru",
    "uz": "uz",
}
def _tts_lang(code: str) -> str:
    return GTTS_LANG_MAP.get(code, code)


async def _send_dual_audio(context, chat_id, original_text, translated_text, src_lang, tgt_lang):
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_VOICE)
    a1, ok1 = await process_text_to_speech(original_text[:300], _tts_lang(src_lang))
    if ok1 and a1:
        bio1 = io.BytesIO(a1); bio1.name = f"orig_{src_lang}.mp3"
        src_name = LANG_INFO.get(src_lang, src_lang.upper())
        await context.bot.send_voice(chat_id=chat_id, voice=bio1, caption=f"🔊 Asl: {src_name}")
    a2, ok2 = await process_text_to_speech(translated_text[:300], _tts_lang(tgt_lang))
    if ok2 and a2:
        bio2 = io.BytesIO(a2); bio2.name = f"trans_{tgt_lang}.mp3"
        tgt_name = LANG_INFO.get(tgt_lang, tgt_lang.upper())
        await context.bot.send_voice(chat_id=chat_id, voice=bio2, caption=f"🔊 Tarjima: {tgt_name}")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    text    = update.message.text.strip()
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    state   = context.user_data.get('state', 'main')

    lang = await get_user_lang(user_id)
    t    = lambda k, **kw: get_trans(lang, k, **kw)

    # ── Identify button key in any language ───────────────────────────────
    btn_key = get_button_key(text)

    # ── Main Menu ─────────────────────────────────────────────────────────
    if btn_key == "btn_main_menu" or text == "🏠 Main Menu":
        context.user_data['state'] = "main"
        await update.message.reply_text("🏠", reply_markup=get_main_menu(lang))
        return

    # ── Grammar ───────────────────────────────────────────────────────────
    if btn_key == "btn_grammar":
        from bot.handlers.grammar import show_grammar_menu
        await show_grammar_menu(update, context)
        return

    # ── Tenses ────────────────────────────────────────────────────────────
    if btn_key == "btn_tenses":
        from bot.handlers.tenses import show_tenses_menu
        await show_tenses_menu(update, context)
        return

    # ── Tests ─────────────────────────────────────────────────────────────
    if btn_key == "btn_tests":
        from bot.handlers.tests import show_test_menu
        await show_test_menu(update.message, context, lang)
        return

    # ── Video Lessons ─────────────────────────────────────────────────────
    if btn_key == "btn_videos":
        from bot.handlers.video_lessons import handle_video_lessons
        await handle_video_lessons(update, context)
        return

    # ── Games ─────────────────────────────────────────────────────────────
    if btn_key == "btn_games":
        from bot.handlers.games import handle_games_menu
        await handle_games_menu(update, context)
        return

    # ── History ───────────────────────────────────────────────────────────
    if btn_key == "btn_history":
        from bot.handlers.callbacks import show_history
        await show_history(update, context)
        return

    # ── Vocabulary ────────────────────────────────────────────────────────
    if btn_key == "btn_vocabulary":
        from bot.handlers.vocabulary import start_vocabulary
        await start_vocabulary(update, context)
        return

    # ── AI Chat ───────────────────────────────────────────────────────────
    if btn_key == "btn_ai":
        context.user_data['state'] = "ai_chat"
        await update.message.reply_text(
            "🤖 *AI Chat* — Savolingizni yozing (ingliz tili bo'yicha):",
            parse_mode="Markdown"
        )
        return

    # ── Role Play ─────────────────────────────────────────────────────────
    if btn_key == "btn_roleplay":
        context.user_data['state'] = "roleplay"
        await update.message.reply_text(
            "🎭 *Role Play* — ssenariyni tanlang:",
            parse_mode="Markdown",
            reply_markup=get_roleplay_menu(lang)
        )
        return

    # ── Other Languages ───────────────────────────────────────────────────
    if btn_key == "btn_other_lang":
        context.user_data['state'] = "other_lang"
        await update.message.reply_text(
            "🌍 Qaysi tilga tarjima qilish kerak?",
            reply_markup=get_other_languages_buttons()
        )
        return

    # ── Translator mode select ─────────────────────────────────────────────
    if btn_key in ("btn_translator", "btn_voice", "btn_photo", "btn_file"):
        context.user_data['state'] = "main"
        msgs = {
            "btn_translator": t("send_text"),
            "btn_voice":      t("send_voice"),
            "btn_photo":      t("send_photo"),
            "btn_file":       t("send_file"),
        }
        await update.message.reply_text(f"✅ {msgs[btn_key]}")
        return

    # ── Status ────────────────────────────────────────────────────────────
    if btn_key == "btn_status":
        from bot.handlers.status import show_status
        await show_status(update, context)
        return

    # ── Settings ──────────────────────────────────────────────────────────
    if btn_key == "btn_settings":
        await update.message.reply_text(
            f"*{t('settings_title')}*\n\n{t('settings_text')}",
            parse_mode="Markdown",
            reply_markup=get_settings_keyboard(lang)
        )
        return

    # ── About Us ──────────────────────────────────────────────────────────
    if btn_key == "btn_about":
        await update.message.reply_text(t("about_text"), parse_mode="Markdown")
        return

    # ── Grammar / Tenses topic selection ─────────────────────────────────
    if text in GRAMMAR_DATA:
        await handle_grammar_selection(update, context)
        return

    if text in TENSE_MAPPING:
        await handle_tense_selection(update, context)
        return

    # ── Name input (during /start setup or from settings) ──────────────────
    if state == "awaiting_name":
        name = text.strip()[:50]
        if not name:
            await update.message.reply_text("❌ Iltimos, ismingizni kiriting:")
            return

        # Save name as nickname in DB
        db = await get_db_connection()
        try:
            await db.execute("UPDATE users SET nickname = ? WHERE user_id = ?", (name, user_id))
            await db.commit()
        finally:
            await db.close()

        setup_step = context.user_data.get('setup_step', 'name')

        if setup_step == "change_name":
            # User is changing name from settings
            context.user_data['state'] = "main"
            context.user_data.pop('setup_step', None)
            await update.message.reply_text(
                f"✅ Ism muvaffaqiyatli o'zgartirildi!\n\n"
                f"👤 Yangi ismingiz: *{name}*\n\n"
                f"📌 Eslatma: Ismingiz xush kelish xabarida ko'rinadi.",
                parse_mode="Markdown"
            )
            return

        # New user: after saving name, ask for language selection
        context.user_data['state'] = "choosing_language"
        context.user_data.pop('setup_step', None)
        from bot.utils.keyboards import get_language_selection_keyboard
        await update.message.reply_text(
            f"✅ *{name}*, tanishingiz bilan xursandman!\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🌐 *Tilni tanlang / Select your language / Выберите язык:*\n\n"
            f"Choose the language for the bot interface.\n"
            f"Bot interfeysi uchun tilni tanlang:",
            parse_mode="Markdown",
            reply_markup=get_language_selection_keyboard()
        )
        return

    # ── Custom quiz topic input ────────────────────────────────────────────
    if state == "awaiting_custom_topic":
        from bot.handlers.tests import show_count_menu
        context.user_data['quiz_step'] = 'choosing_count'
        await show_count_menu(update.message, context, text, lang)
        return

    # ── Nickname input ─────────────────────────────────────────────────────
    if state == "awaiting_nickname":
        nick = text[:30]
        db = await get_db_connection()
        try:
            await db.execute("UPDATE users SET nickname = ? WHERE user_id = ?", (nick, user_id))
            await db.commit()
        finally:
            await db.close()
        context.user_data['state'] = "main"
        await update.message.reply_text(t("nickname_set", nick=nick))
        return

    # ── AI Chat ────────────────────────────────────────────────────────────
    if state == "ai_chat":
        from bot.ai.openrouter import ask_openrouter
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        sys_prompt = (
            "You are an expert English teacher. "
            "Answer in the user's native language if possible. "
            "Be clear, give examples, and use Uzbek for Uzbek users."
        )
        res = await ask_openrouter(text, system_prompt=sys_prompt)
        await update.message.reply_text(res or t("error_generic"))
        return

    # ── Role Play ──────────────────────────────────────────────────────────
    if state == "roleplay":
        from bot.handlers.roleplay import handle_roleplay_text
        await handle_roleplay_text(update, context)
        return

    # ── Other language mode ────────────────────────────────────────────────
    if state == "other_lang":
        target_lang = context.user_data.get('target_lang', 'ru')
        detected    = detect_language(text)

        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        translated = await translate_text(text, source="auto", target=target_lang)

        db = await get_db_connection()
        try:
            await db.execute(
                "INSERT INTO history (user_id, original, translated, mode) VALUES (?, ?, ?, ?)",
                (chat_id, text, translated, "text")
            )
            await db.commit()
            cursor = await db.execute("SELECT last_insert_rowid()")
            last_id = (await cursor.fetchone())[0]
        finally:
            await db.close()

        tgt_name = LANG_INFO.get(target_lang, target_lang.upper())
        res_msg  = (
            f"🌍 *{tgt_name} tarjimasi*\n\n"
            f"📝 Asl:\n{text}\n\n"
            f"✅ {tgt_name}:\n{translated}"
        )
        await update.message.reply_text(res_msg, parse_mode="Markdown",
                                         reply_markup=get_audio_button(str(last_id)))
        await _send_dual_audio(context, chat_id, text, translated, detected, target_lang)
        return

    # ── Default: uz ↔ en translation ──────────────────────────────────────
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    detected   = detect_language(text)
    target     = "uz" if detected.startswith("en") else "en"
    translated = await translate_text(text, source="auto", target=target)

    db = await get_db_connection()
    try:
        await db.execute(
            "INSERT INTO history (user_id, original, translated, mode) VALUES (?, ?, ?, ?)",
            (chat_id, text, translated, "text")
        )
        await db.commit()
        cursor = await db.execute("SELECT last_insert_rowid()")
        last_id = (await cursor.fetchone())[0]
    finally:
        await db.close()

    dir_label = "O'zbekcha" if detected.startswith("uz") else "Inglizcha"
    target_name = "Inglizcha" if target == "en" else "O'zbekcha"
    res_msg   = (
        f"🌐 *Translation*\n\n"
        f"📝 Original ({dir_label}):\n{text}\n\n"
        f"✅ {target_name}:\n{translated}"
    )
    await update.message.reply_text(res_msg, parse_mode="Markdown",
                                     reply_markup=get_audio_button(str(last_id)))
