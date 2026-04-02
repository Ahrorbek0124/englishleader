import io
import logging

logger = logging.getLogger(__name__)


def convert_ogg_to_wav(ogg_bytes: bytes) -> bytes:
    """
    OGG audio baytlarini WAV formatiga o'giradi.
    pydub + ffmpeg yoki fallback sifatida avconv ishlatadi.
    """
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_ogg(io.BytesIO(ogg_bytes))
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        return wav_io.getvalue()
    except Exception as e:
        logger.error(f"pydub OGG→WAV failed: {e}. Trying raw bytes fallback.")
        # Agar pydub ishlamasa, baytlarni to'g'ridan-to'g'ri qaytarish
        # (Groq Whisper ko'p formatlarni qabul qiladi)
        return ogg_bytes


def mp3_to_ogg(mp3_bytes: bytes) -> bytes:
    """
    MP3 baytlarini Telegram Voice uchun OGG/OPUS formatiga o'giradi.
    Telegram send_voice uchun OGG tavsiya etiladi.
    """
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_mp3(io.BytesIO(mp3_bytes))
        ogg_io = io.BytesIO()
        audio.export(ogg_io, format="ogg", codec="libopus",
                     parameters=["-vbr", "on", "-compression_level", "10"])
        return ogg_io.getvalue()
    except Exception as e:
        logger.warning(f"MP3→OGG conversion failed: {e}. Sending as MP3.")
        return mp3_bytes  # Telegram MP3 ni ham qabul qiladi
