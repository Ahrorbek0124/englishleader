import aiohttp
import json
from typing import Optional

from bot.config import DEEPGRAM_API_KEY

async def transcribe_audio_deepgram(audio_bytes: bytes) -> tuple[Optional[str], str]:
    """
    Transcribe audio using Deepgram.
    Returns (transcribed_text, error_message).
    """
    if not DEEPGRAM_API_KEY:
        return None, "Deepgram API key not configured."

    url = "https://api.deepgram.com/v1/listen?detect_language=true&punctuate=true"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "audio/ogg" # Telegram sends OGG format
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=audio_bytes, timeout=30) as response:
                if response.status != 200:
                    err_txt = await response.text()
                    return None, f"Deepgram Error {response.status}: {err_txt}"
                
                data = await response.json()
                results = data.get("results", {})
                channels = results.get("channels", [])
                if not channels:
                    return None, "No audio channels detected."
                
                alternatives = channels[0].get("alternatives", [])
                if not alternatives:
                    return None, "No transcription alternatives found."
                
                transcript = alternatives[0].get("transcript", "")
                if not transcript.strip():
                    return None, "Empty transcription result."
                    
                return transcript, ""
    except Exception as e:
        return None, f"Deepgram exception: {e}"
