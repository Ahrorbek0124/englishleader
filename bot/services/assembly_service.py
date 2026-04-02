import aiohttp
import asyncio
from typing import Optional

from bot.config import ASSEMBLYAI_API_KEY

async def transcribe_audio_assemblyai(audio_bytes: bytes) -> tuple[Optional[str], str]:
    """
    Transcribe audio using AssemblyAI as a fallback.
    Returns (transcribed_text, error_message).
    """
    if not ASSEMBLYAI_API_KEY:
        return None, "AssemblyAI API key not configured."

    upload_url = "https://api.assemblyai.com/v2/upload"
    transcript_url = "https://api.assemblyai.com/v2/transcript"
    
    headers = {
        "authorization": ASSEMBLYAI_API_KEY,
        "content-type": "application/octet-stream"
    }

    try:
        async with aiohttp.ClientSession() as session:
            # 1. Upload audio
            async with session.post(upload_url, headers=headers, data=audio_bytes, timeout=30) as upload_resp:
                if upload_resp.status != 200:
                    err = await upload_resp.text()
                    return None, f"Assembly Upload Error {upload_resp.status}: {err}"
                upload_res = await upload_resp.json()
                audio_url = upload_res.get("upload_url")
                if not audio_url:
                    return None, "Failed to get upload URL from AssemblyAI."

            # 2. Request transcription
            json_data = {"audio_url": audio_url, "language_detection": True}
            async with session.post(transcript_url, json=json_data, headers={"authorization": headers["authorization"]}) as trans_resp:
                if trans_resp.status != 200:
                    err = await trans_resp.text()
                    return None, f"Assembly Transcript Error {trans_resp.status}: {err}"
                trans_res = await trans_resp.json()
                transcript_id = trans_res.get("id")

            # 3. Poll for completion
            polling_endpoint = f"{transcript_url}/{transcript_id}"
            for _ in range(30): # Timeout after roughly 60 seconds
                await asyncio.sleep(2)
                async with session.get(polling_endpoint, headers={"authorization": headers["authorization"]}) as poll_resp:
                    poll_res = await poll_resp.json()
                    status = poll_res.get("status")
                    
                    if status == "completed":
                        return poll_res.get("text", ""), ""
                    elif status == "error":
                        return None, f"Assembly Task Error: {poll_res.get('error')}"
            
            return None, "AssemblyAI transcription timed out."
            
    except Exception as e:
        return None, f"AssemblyAI exception: {e}"
