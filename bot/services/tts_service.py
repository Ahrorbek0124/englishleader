import asyncio
import io
import logging
from bot.services.muxlisa_service import uzbek_tts

logger = logging.getLogger(__name__)

# gTTS til kodlari xaritasi (ba'zi tillar maxsus kod talab qiladi)
GTTS_LANG_MAP = {
    "zh-CN": "zh-CN",
    "zh-TW": "zh-TW",
    "zh": "zh-CN",
    "he": "iw",       # Hebrew eski kodi bilan ham ishlaydi
    "jw": "jw",       # Javanese
    "uz": "uz",
}

async def gtts_tts(text: str, lang: str) -> bytes | None:
    """gTTS orqali har qanday til uchun audio yasaydi."""
    try:
        from gtts import gTTS
        gtts_lang = GTTS_LANG_MAP.get(lang, lang)

        def _gen():
            t = gTTS(text=text, lang=gtts_lang, slow=False)
            b = io.BytesIO()
            t.write_to_fp(b)
            return b.getvalue()

        return await asyncio.to_thread(_gen)
    except Exception as e:
        logger.error(f"gTTS failed lang={lang}: {e}")
        # Inglizchaga fallback
        if lang != "en":
            try:
                from gtts import gTTS
                def _gen_en():
                    t = gTTS(text=text, lang="en", slow=False)
                    b = io.BytesIO()
                    t.write_to_fp(b)
                    return b.getvalue()
                return await asyncio.to_thread(_gen_en)
            except Exception:
                pass
        return None

async def process_text_to_speech(text: str, lang: str) -> tuple[bytes | None, bool]:
    """
    Barcha tillar uchun TTS.
    uz → Muxlisa (o'zbek ovozi) → gTTS fallback
    boshqalar → gTTS
    """
    # O'zbek tili uchun Muxlisa
    if lang in ("uz", "uz-UZ"):
        audio = await uzbek_tts(text)
        if audio:
            return audio, True
        # Muxlisa ishlamasa gTTS uz
        audio = await gtts_tts(text, "uz")
        return audio, (audio is not None)

    # Barcha boshqa tillar uchun gTTS
    audio = await gtts_tts(text, lang)
    return audio, (audio is not None)
