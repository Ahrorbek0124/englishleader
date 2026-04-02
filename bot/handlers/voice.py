import io
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from bot.services.stt_service import process_voice_to_text
from bot.services.translator_service import translate_text, detect_language
from bot.services.tts_service import process_text_to_speech
from bot.utils.audio_utils import convert_ogg_to_wav
from bot.utils.keyboards import get_audio_button, LANG_INFO
from bot.database.db import get_db_connection, get_user_lang
from bot.services.i18n import get_trans


async def _send_voice_safe(context, chat_id: int, audio_bytes: bytes, lang: str, caption: str):
    try:
        bio = io.BytesIO(audio_bytes)
        bio.name = f"audio_{lang}.mp3"
        await context.bot.send_voice(chat_id=chat_id, voice=bio, caption=caption)
    except Exception:
        try:
            bio2 = io.BytesIO(audio_bytes)
            bio2.name = f"audio_{lang}.mp3"
            await context.bot.send_audio(chat_id=chat_id, audio=bio2, caption=caption)
        except Exception:
            pass


# ─── Map language codes to gTTS-compatible codes ────────────────────────────
GTTS_LANG_MAP = {
    "zh-CN": "zh-CN", "zh": "zh-CN",
    "he":    "iw",
    "kk":    "ru",   # Kazakh fallback to Russian (gTTS doesn't support kk)
    "ne":    "ne",
    "ur":    "ur",
    "fa":    "fa",
    "uz":    "uz",
}


def _tts_lang(lang_code: str) -> str:
    """Get the best TTS lang code for a given language."""
    return GTTS_LANG_MAP.get(lang_code, lang_code)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.voice:
        return
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    user_lang = await get_user_lang(user_id)
    t = lambda k, **kw: get_trans(user_lang, k, **kw)

    await update.message.reply_text(t("voice_processing"))
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    # ── Download & convert to WAV ──────────────────────────────────────────
    try:
        file = await context.bot.get_file(update.message.voice.file_id)
        ogg_bytes = bytes(await file.download_as_bytearray())
        wav_bytes = convert_ogg_to_wav(ogg_bytes)
    except Exception as e:
        await update.message.reply_text(f"❌ Ovoz yuklashda xatolik: {e}")
        return

    # ── Speech-to-Text ────────────────────────────────────────────────────
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    transcribed, ok = await process_voice_to_text(wav_bytes)
    if not ok:
        await update.message.reply_text(transcribed)
        return

    # ── Determine translation direction ──────────────────────────────────
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    state   = context.user_data.get('state', 'main')
    detected = detect_language(transcribed)

    if state == "other_lang":
        target = context.user_data.get('target_lang', 'ru')
    else:
        # Default: uz ↔ en
        target = "uz" if detected.startswith("en") else "en"

    translated = await translate_text(transcribed, source="auto", target=target)

    # ── Save to history ───────────────────────────────────────────────────
    db = await get_db_connection()
    try:
        await db.execute(
            "INSERT INTO history (user_id, original, translated, mode) VALUES (?, ?, ?, ?)",
            (chat_id, transcribed, translated, "voice")
        )
        await db.commit()
        cursor = await db.execute("SELECT last_insert_rowid()")
        last_id = (await cursor.fetchone())[0]
    finally:
        await db.close()

    # ── Send text result ──────────────────────────────────────────────────
    src_name = LANG_INFO.get(detected, detected.upper())
    tgt_name = LANG_INFO.get(target, target.upper())

    result_msg = (
        f"🎤 *Ovoz Tarjimasi*\n\n"
        f"🔤 Aniqlangan til: {src_name}\n"
        f"📝 Matn:\n{transcribed}\n\n"
        f"🌐 {tgt_name} tarjimasi:\n{translated}"
    )
    await update.message.reply_text(result_msg, parse_mode="Markdown",
                                    reply_markup=get_audio_button(str(last_id)))

    # ── TTS: original voice ───────────────────────────────────────────────
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_VOICE)

    # FIXED: use the ACTUAL detected language for TTS, not hardcoded "en"/"uz"
    src_tts_lang = _tts_lang(detected)
    a1, ok1 = await process_text_to_speech(transcribed[:300], src_tts_lang)
    if ok1 and a1:
        await _send_voice_safe(context, chat_id, a1, src_tts_lang,
                               f"🔊 Asl ovoz: {src_name}")

    # ── TTS: translated voice ─────────────────────────────────────────────
    tgt_tts_lang = _tts_lang(target)
    a2, ok2 = await process_text_to_speech(translated[:300], tgt_tts_lang)
    if ok2 and a2:
        await _send_voice_safe(context, chat_id, a2, tgt_tts_lang,
                               f"🔊 Tarjima ovozi: {tgt_name}")
