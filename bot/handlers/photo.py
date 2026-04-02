import io
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from bot.services.ocr_service import process_image_ocr
from bot.services.translator_service import translate_text, detect_language
from bot.services.tts_service import process_text_to_speech
from bot.utils.image_utils import create_translated_image
from bot.utils.keyboards import get_audio_button
from bot.database.db import get_db_connection, get_user_lang
from bot.services.i18n import get_trans

# ── TTS lang map (same as voice.py) ──────────────────────────────────────────
GTTS_LANG_MAP = {
    "zh-CN": "zh-CN", "zh": "zh-CN",
    "he": "iw",
    "kk": "ru",
    "uz": "uz",
}

def _tts_lang(lang_code: str) -> str:
    return GTTS_LANG_MAP.get(lang_code, lang_code)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.photo:
        return
    chat_id  = update.effective_chat.id
    user_id  = update.effective_user.id
    user_lang = await get_user_lang(user_id)
    t = lambda k, **kw: get_trans(user_lang, k, **kw)

    await update.message.reply_text(t("ocr_processing"))
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    # ── Download image ─────────────────────────────────────────────────────
    photo         = update.message.photo[-1]
    photo_file    = await context.bot.get_file(photo.file_id)
    raw_img_bytes = bytes(await photo_file.download_as_bytearray())

    # ── OCR ───────────────────────────────────────────────────────────────
    extracted, ok = await process_image_ocr(raw_img_bytes)
    if not ok:
        await update.message.reply_text(f"❌ {extracted}")
        return

    # ── Translate ─────────────────────────────────────────────────────────
    await update.message.reply_text(t("translating"))
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    detected = detect_language(extracted)
    target   = "uz" if detected.startswith("en") else "en"
    translated = await translate_text(extracted, source="auto", target=target)

    # ── Save history ──────────────────────────────────────────────────────
    db = await get_db_connection()
    try:
        await db.execute(
            "INSERT INTO history (user_id, original, translated, mode) VALUES (?, ?, ?, ?)",
            (chat_id, extracted, translated, "photo")
        )
        await db.commit()
        cursor = await db.execute("SELECT last_insert_rowid()")
        last_id = (await cursor.fetchone())[0]
    finally:
        await db.close()

    # ── Text result ───────────────────────────────────────────────────────
    lang_label = "Inglizcha → O'zbekcha" if target == "uz" else "O'zbekcha → Inglizcha"
    caption = (
        f"📷 *Photo Translator* ({lang_label})\n\n"
        f"🔍 *Aniqlangan matn:*\n{extracted[:400]}"
        f"{'...' if len(extracted) > 400 else ''}\n\n"
        f"✅ *Tarjima:*\n{translated[:400]}"
        f"{'...' if len(translated) > 400 else ''}"
    )
    await update.message.reply_text(caption, parse_mode="Markdown",
                                    reply_markup=get_audio_button(str(last_id)))

    # ── Send translated image overlay (original text + translation shown) ──
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)
    try:
        translated_img = create_translated_image(
            original_bytes=raw_img_bytes,
            original_text=extracted,
            translated_text=translated,
            target_lang=target
        )
        bio = io.BytesIO(translated_img)
        bio.name = "translated_photo.jpg"
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=bio,
            caption=f"🖼️ Tarjima qilingan rasm ({lang_label})"
        )
    except Exception as e:
        pass  # Text result is enough if image fails

    # ── TTS: original voice ───────────────────────────────────────────────
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_VOICE)

    src_tts = _tts_lang(detected if detected else "en")
    a1, ok1 = await process_text_to_speech(extracted[:300], src_tts)
    if ok1 and a1:
        bio1 = io.BytesIO(a1); bio1.name = f"original_{src_tts}.mp3"
        await context.bot.send_voice(chat_id=chat_id, voice=bio1,
                                     caption=f"🔊 Asl matn ovozi")

    # ── TTS: translation voice ─────────────────────────────────────────────
    tgt_tts = _tts_lang(target)
    a2, ok2 = await process_text_to_speech(translated[:300], tgt_tts)
    if ok2 and a2:
        bio2 = io.BytesIO(a2); bio2.name = f"translated_{tgt_tts}.mp3"
        await context.bot.send_voice(chat_id=chat_id, voice=bio2,
                                     caption=f"🔊 Tarjima ovozi ({target.upper()})")
