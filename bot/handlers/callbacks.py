import io
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from bot.services.tts_service import process_text_to_speech
from bot.database.db import get_db_connection, get_user_lang, set_user_lang
from bot.utils.keyboards import (
    get_other_languages_buttons, LANG_INFO,
    get_language_selection_keyboard, get_main_menu, get_settings_keyboard,
    get_status_keyboard
)
from bot.services.i18n import get_trans, TRANSLATIONS

# TTS lang map
GTTS_LANG_MAP = {
    "zh-CN": "zh-CN", "zh": "zh-CN",
    "he": "iw",
    "kk": "ru",
    "uz": "uz",
}
def _tts_lang(code: str) -> str:
    return GTTS_LANG_MAP.get(code, code)


async def _get_user_name(user_id: int) -> str:
    """Get user's display name: nickname > first_name from DB."""
    db = await get_db_connection()
    try:
        cursor = await db.execute(
            "SELECT nickname, first_name FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            return row["nickname"] or row["first_name"] or "Friend"
    except Exception:
        pass
    finally:
        await db.close()
    return "Friend"


async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query   = update.callback_query
    await query.answer()
    data    = query.data
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    lang    = await get_user_lang(user_id)
    t       = lambda k, **kw: get_trans(lang, k, **kw)

    # ── Language selection at startup ──────────────────────────────────────
    if data.startswith("setlang_"):
        chosen_lang = data.replace("setlang_", "")
        await set_user_lang(user_id, chosen_lang)
        lang_name = LANG_INFO.get(chosen_lang, chosen_lang)

        # Register user properly
        user = query.from_user
        db = await get_db_connection()
        try:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username, first_name, lang, last_active) "
                "VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                (user.id, user.username, user.first_name, chosen_lang)
            )
            await db.execute(
                "UPDATE users SET lang = ?, last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
                (chosen_lang, user.id)
            )
            await db.commit()
        finally:
            await db.close()

        # Get user's name for welcome message
        name = await _get_user_name(user_id)
        welcome = get_trans(chosen_lang, "welcome", name=name)

        context.user_data['state'] = "main"
        await query.message.reply_text(welcome, reply_markup=get_main_menu(chosen_lang))
        try:
            await query.message.delete()
        except Exception:
            pass
        return

    # ── Settings callbacks ─────────────────────────────────────────────────
    if data == "settings_lang":
        await query.message.reply_text(
            t("choose_lang"),
            reply_markup=get_language_selection_keyboard()
        )
        return

    if data == "settings_name":
        context.user_data['state'] = "awaiting_name"
        context.user_data['setup_step'] = "change_name"
        current_name = await _get_user_name(user_id)
        await query.message.reply_text(
            f"✏️ *Ismni o'zgartirish / Change Name*\n\n"
            f"👤 Hozirgi ismingiz: *{current_name}*\n\n"
            f"📝 Yangi ismingizni kiriting:",
            parse_mode="Markdown"
        )
        return

    if data == "settings_nick":
        context.user_data['state'] = "awaiting_nickname"
        await query.message.reply_text(t("enter_nickname"))
        return

    if data == "settings_reset":
        db = await get_db_connection()
        try:
            await db.execute(
                "UPDATE users SET level='A1', streak=0 WHERE user_id=?", (user_id,)
            )
            await db.execute("DELETE FROM test_results WHERE user_id=?", (user_id,))
            await db.execute("DELETE FROM user_topics WHERE user_id=?", (user_id,))
            await db.commit()
        finally:
            await db.close()
        await query.message.reply_text(t("status_reset"))
        return

    # ── Status callbacks ───────────────────────────────────────────────────
    if data == "status_learned":
        from bot.handlers.status import show_learned_topics
        await show_learned_topics(query.message, context, lang, user_id=user_id)
        return

    if data == "status_pending":
        from bot.handlers.status import show_pending_topics
        await show_pending_topics(query.message, context, lang, user_id=user_id)
        return

    # ── Mark topic as learned ──────────────────────────────────────────────
    if data.startswith("learned_grammar_") or data.startswith("learned_tense_"):
        if data.startswith("learned_grammar_"):
            topic_key  = data.replace("learned_grammar_", "").replace("_", " ")
        else:
            tense_id   = int(data.replace("learned_tense_", ""))
            from bot.handlers.tenses import TENSES_DATA
            tense_info = TENSES_DATA.get(tense_id, {})
            topic_key  = f"Tense_{tense_id}"
            # Extract name from tense data first line
            first_line = str(tense_info).split("\\n")[0] if tense_info else f"Tense {tense_id}"
            topic_key  = first_line[:50]

        db = await get_db_connection()
        try:
            await db.execute(
                "INSERT OR IGNORE INTO user_topics (user_id, topic_key, topic_name) VALUES (?, ?, ?)",
                (user_id, topic_key, topic_key)
            )
            await db.commit()
        finally:
            await db.close()
        await query.message.reply_text(t("topic_learned", topic=topic_key))
        return

    # ── Audio playback ─────────────────────────────────────────────────────
    if data.startswith("audio_"):
        history_id = data.split("_")[1]
        db = await get_db_connection()
        try:
            cursor = await db.execute(
                "SELECT original, translated FROM history WHERE id = ?", (history_id,)
            )
            row = await cursor.fetchone()
        finally:
            await db.close()

        if not row:
            await query.message.reply_text("❌ Tarjima konteksti topilmadi.")
            return

        from bot.services.translator_service import detect_language
        text1, text2 = row['original'], row['translated']
        lang1 = detect_language(text1)
        lang2 = detect_language(text2)

        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_VOICE)

        a1, ok1 = await process_text_to_speech(text1, _tts_lang(lang1))
        if ok1 and a1:
            bio1 = io.BytesIO(a1); bio1.name = f"{lang1}.mp3"
            await context.bot.send_voice(chat_id=chat_id, voice=bio1,
                                          caption=f"🔊 Asl matn ({lang1.upper()})")

        a2, ok2 = await process_text_to_speech(text2, _tts_lang(lang2))
        if ok2 and a2:
            bio2 = io.BytesIO(a2); bio2.name = f"{lang2}.mp3"
            await context.bot.send_voice(chat_id=chat_id, voice=bio2,
                                          caption=f"🔊 Tarjima ({lang2.upper()})")

        if not ok1 and not ok2:
            await query.message.reply_text("❌ Audio yaratishda xatolik.")
        return

    # ── Save word ──────────────────────────────────────────────────────────
    if data.startswith("save_"):
        history_id = data.split("_")[1]
        db = await get_db_connection()
        try:
            cursor = await db.execute(
                "SELECT original, translated FROM history WHERE id = ?", (history_id,)
            )
            row = await cursor.fetchone()
            if row:
                word  = row['original'][:50]
                trans = row['translated'][:50]
                await db.execute(
                    "INSERT INTO saved_words (user_id, word, translation, next_review) "
                    "VALUES (?, ?, ?, date('now', '+1 day'))",
                    (chat_id, word, trans)
                )
                await db.commit()
                await query.message.reply_text(f"💾 Saqlandi: {word} → {trans}")
            else:
                await query.message.reply_text("❌ Ma'lumot topilmadi.")
        finally:
            await db.close()
        return

    # ── Delete history entry ───────────────────────────────────────────────
    if data.startswith("del_"):
        history_id = data.split("_")[1]
        db = await get_db_connection()
        try:
            await db.execute("DELETE FROM history WHERE id = ?", (history_id,))
            await db.commit()
            await query.message.reply_text("🗑 O'chirildi.")
        finally:
            await db.close()
        return

    # ── Grammar quiz ───────────────────────────────────────────────────────
    if data.startswith("quiz_grammar_"):
        topic_id = data.replace("quiz_grammar_", "").replace("_", " ")
        from bot.handlers.tests import show_count_menu
        await show_count_menu(query.message, context, topic_id, lang)
        return

    # ── Ask AI about grammar topic ─────────────────────────────────────────
    if data.startswith("ask_ai_"):
        topic_id = data.replace("ask_ai_", "").replace("_", " ")
        context.user_data['state'] = "ai_chat"
        await query.message.reply_text(
            f"🤖 AI Chat rejimi. Mavzu: *{topic_id}*\nSavolingizni yozing:",
            parse_mode="Markdown"
        )
        return

    # ── Tense navigation ───────────────────────────────────────────────────
    if data.startswith("tense_") and not data.startswith("tense_quiz"):
        tense_id = int(data.split("_")[1])
        from bot.handlers.tenses import show_tense_info
        await show_tense_info(update, context, tense_id)
        return

    # ── Tense quiz ─────────────────────────────────────────────────────────
    if data.startswith("quiz_tense_"):
        tense_id = data.replace("quiz_tense_", "")
        from bot.handlers.tests import show_count_menu
        await show_count_menu(query.message, context, f"Tense ID: {tense_id}", lang)
        return

    # ── Target language selection for "Other Languages" ────────────────────
    if data.startswith("lang_"):
        lang_code = data.replace("lang_", "")
        context.user_data['target_lang'] = lang_code
        context.user_data['state']       = "other_lang"
        lang_name = LANG_INFO.get(lang_code, lang_code)
        await query.message.reply_text(
            f"✅ Til tanlandi: *{lang_name}*\n\n"
            f"Endi matn yuboring — men uni {lang_name} tiliga tarjima qilaman.\n\n"
            f"Boshqa til: 🌍 Boshqa tillar",
            parse_mode="Markdown"
        )
        return


async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    db = await get_db_connection()
    try:
        cursor = await db.execute(
            "SELECT id, original, translated, mode, created_at FROM history "
            "WHERE user_id = ? ORDER BY id DESC LIMIT 20",
            (chat_id,)
        )
        rows = await cursor.fetchall()
    finally:
        await db.close()

    if not rows:
        await update.message.reply_text("📜 Tarixingiz bo'sh.")
        return

    from bot.utils.keyboards import get_history_buttons
    icons = {'text': '📝', 'voice': '🎤', 'photo': '📷', 'file': '📄'}
    for row in reversed(rows):
        icon = icons.get(row['mode'], '📝')
        date = str(row['created_at'] or "").split()[0] or "?"
        msg = (
            f"{icon} [{date}]\n"
            f"📥 {row['original'][:80]}\n"
            f"📤 {row['translated'][:80]}"
        )
        await update.message.reply_text(msg, reply_markup=get_history_buttons(str(row['id'])))
