import aiohttp
import asyncio
import logging
from bot.config import DEEPGRAM_API_KEY, ASSEMBLYAI_API_KEY, GROQ_API_KEY
from bot.services.muxlisa_service import transcribe_muxlisa

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# 1. GROQ WHISPER — eng aniq va tez (bepul)
# ──────────────────────────────────────────────
async def groq_whisper_stt(audio_bytes: bytes, filename: str = "audio.wav") -> tuple[str | None, str | None]:
    if not GROQ_API_KEY:
        return None, "Groq API key missing"

    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}

    form = aiohttp.FormData()
    form.add_field("file", audio_bytes, filename=filename, content_type="audio/wav")
    form.add_field("model", "whisper-large-v3")
    form.add_field("response_format", "text")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=form,
                                    timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    text = (await resp.text()).strip()
                    if text:
                        logger.info("Groq Whisper STT OK")
                        return text, None
                    return None, "Empty transcription"
                err = await resp.text()
                logger.error(f"Groq Whisper {resp.status}: {err[:200]}")
                return None, f"Groq {resp.status}"
    except Exception as e:
        logger.error(f"Groq Whisper exception: {e}")
        return None, str(e)


# ──────────────────────────────────────────────
# 2. DEEPGRAM — fallback 1
# ──────────────────────────────────────────────
async def deepgram_stt(audio_bytes: bytes) -> tuple[str | None, str | None]:
    if not DEEPGRAM_API_KEY:
        return None, "Deepgram key missing"

    url = "https://api.deepgram.com/v1/listen?language=multi&model=nova-2&smart_format=true"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "audio/wav"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=audio_bytes,
                                    timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    text = (data.get("results", {})
                            .get("channels", [{}])[0]
                            .get("alternatives", [{}])[0]
                            .get("transcript", ""))
                    return (text, None) if text else (None, "Empty result")
                return None, await resp.text()
    except Exception as e:
        logger.error(f"Deepgram failed: {e}")
        return None, str(e)


# ──────────────────────────────────────────────
# 3. ASSEMBLYAI — fallback 2
# ──────────────────────────────────────────────
async def assembly_stt(audio_bytes: bytes) -> tuple[str | None, str | None]:
    if not ASSEMBLYAI_API_KEY:
        return None, "Assembly key missing"

    upload_url = "https://api.assemblyai.com/v2/upload"
    headers = {"Authorization": ASSEMBLYAI_API_KEY}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(upload_url, headers=headers, data=audio_bytes,
                                    timeout=aiohttp.ClientTimeout(total=15)) as up:
                if up.status != 200:
                    return None, "Upload failed"
                audio_url = (await up.json()).get("upload_url")

            async with session.post(
                "https://api.assemblyai.com/v2/transcript",
                headers=headers,
                json={"audio_url": audio_url, "language_detection": True},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as tr:
                if tr.status != 200:
                    return None, "Transcript request failed"
                transcript_id = (await tr.json()).get("id")

            for _ in range(20):
                await asyncio.sleep(3)
                async with session.get(
                    f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                    headers=headers
                ) as poll:
                    data = await poll.json()
                    if data.get("status") == "completed":
                        return data.get("text"), None
                    if data.get("status") == "error":
                        return None, "Assembly error"
        return None, "Assembly timeout"
    except Exception as e:
        logger.error(f"Assembly failed: {e}")
        return None, str(e)


# ──────────────────────────────────────────────
# UNIFIED — fallback zanjiri
# ──────────────────────────────────────────────
async def process_voice_to_text(audio_bytes: bytes) -> tuple[str, bool]:
    """
    Fallback zanjiri:
    Groq Whisper → Muxlisa → Deepgram → AssemblyAI
    """
    # 1. Groq Whisper (eng aniq)
    text, err = await groq_whisper_stt(audio_bytes)
    if text and text.strip():
        return text.strip(), True

    # 2. Muxlisa (o'zbek uchun yaxshi)
    text, err = await transcribe_muxlisa(audio_bytes)
    if text and text.strip():
        return text.strip(), True

    # 3. Deepgram
    text, err = await deepgram_stt(audio_bytes)
    if text and text.strip():
        return text.strip(), True

    # 4. AssemblyAI
    text, err = await assembly_stt(audio_bytes)
    if text and text.strip():
        return text.strip(), True

    return "⚠️ Ovozingizni aniqlay olmadim. Iltimos, aniqroq va balandroq gapiring yoki matn yuboring.", False
