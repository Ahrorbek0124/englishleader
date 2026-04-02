import aiohttp
import asyncio
from bot.config import MUXLISA_API_KEY
import logging

logger = logging.getLogger(__name__)

async def transcribe_muxlisa(audio_bytes: bytes) -> tuple[str | None, str | None]:
    if not MUXLISA_API_KEY:
        return None, "MUXLISA Key missing"
    url = "https://api.muxlisa.uz/v1/stt"
    headers = {"Authorization": f"Bearer {MUXLISA_API_KEY}"}
    form = aiohttp.FormData()
    form.add_field("file", audio_bytes, filename="audio.wav", content_type="audio/wav")
    form.add_field("language", "uz-UZ")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=form, headers=headers, timeout=30) as r:
                if r.status == 200:
                    data = await r.json()
                    return data.get("text"), None
                return None, await r.text()
    except Exception as e:
        logger.error(f"Muxlisa STT failed: {e}")
        return None, str(e)

async def uzbek_tts(text: str) -> bytes | None:
    if MUXLISA_API_KEY:
        url = "https://api.muxlisa.uz/v1/tts"
        payload = {"text": text, "speaker_id": 1}
        headers = {"Authorization": f"Bearer {MUXLISA_API_KEY}", "Content-Type": "application/json"}
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(url, json=payload, headers=headers, timeout=20) as r:
                    if r.status == 200:
                        return await r.read()
        except Exception as e:
            logger.error(f"Muxlisa TTS failed: {e}")
            pass
            
    # 2. gTTS uz fallback
    try:
        from gtts import gTTS
        import asyncio, io
        def _gen():
            t = gTTS(text=text, lang="uz")
            b = io.BytesIO()
            t.write_to_fp(b)
            return b.getvalue()
        return await asyncio.to_thread(_gen)
    except Exception as e:
        logger.error(f"gTTS UZ fallback failed: {e}")
        return None
