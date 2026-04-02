import base64
import logging
from cachetools import LRUCache
from bot.ai.openrouter import ask_openrouter
from langdetect import detect, DetectorFactory
from deep_translator import GoogleTranslator

DetectorFactory.seed = 0
logger = logging.getLogger(__name__)

translation_cache = LRUCache(maxsize=500)

async def translate_text(text: str, source: str = "auto", target: str = "uz") -> str:
    cache_key = f"{text}_{source}_{target}"
    if cache_key in translation_cache:
        return translation_cache[cache_key]

    try:
        translated = GoogleTranslator(source=source, target=target).translate(text)
        translation_cache[cache_key] = translated
        return translated
    except Exception as e:
        logger.error(f"GoogleTranslator failed: {e}")
        
    # Fallback to OpenRouter
    prompt = f"Translate the following text to {target}. ONLY return the translation, no extra texts or quotes."
    res = await ask_openrouter(text, system_prompt=prompt, temperature=0.1)
    if res:
        translation_cache[cache_key] = res
        return res
        
    return "⚠️ Texnik muammo yuz berdi. Tarjima xizmati vaqtincha ishlamayapti."

def detect_language(text: str) -> str:
    try:
        return detect(text)
    except:
        return "en"

