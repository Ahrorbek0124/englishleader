import aiohttp
import asyncio
import json
import logging
from bot.config import OPENROUTER_API_KEYS, GROQ_API_KEY

logger = logging.getLogger(__name__)

ZAI_BASE_URL = "http://localhost:3456/chat"
ZAI_API_KEY = "Z.ai"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# OpenRouter bepul modellari
FREE_MODELS = [
    "google/gemma-3-27b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "deepseek/deepseek-r1-distill-llama-70b:free",
    "qwen/qwen3-8b:free",
]

# Groq modellari (tezkor va bepul)
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]


async def _try_zai(session: aiohttp.ClientSession, payload: dict) -> str | None:
    """Z.ai (local proxy) API — eng ishonchli, birinchi uriniladi."""
    zai_payload = {
        "messages": payload["messages"],
        "max_tokens": payload.get("max_tokens", 800),
        "temperature": payload.get("temperature", 0.7),
    }
    try:
        async with session.post(
            ZAI_BASE_URL,
            json=zai_payload,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                logger.info("Z.ai proxy OK")
                return data["choices"][0]["message"]["content"].strip()
            else:
                err = await resp.text()
                logger.warning(f"Z.ai proxy {resp.status} — err:{err[:200]}")
                return None
    except Exception as e:
        logger.error(f"Z.ai proxy exception — {e}")
        return None


async def _try_groq(session: aiohttp.ClientSession, model: str, payload: dict) -> str | None:
    """Groq API orqali so'rov yuboradi."""
    if not GROQ_API_KEY:
        return None
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    groq_payload = {
        "model": model,
        "messages": payload["messages"],
        "max_tokens": payload.get("max_tokens", 800),
        "temperature": payload.get("temperature", 0.7)
    }
    try:
        async with session.post(
            GROQ_URL,
            json=groq_payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=20)
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                logger.info(f"Groq OK — model:{model}")
                return data["choices"][0]["message"]["content"].strip()
            elif resp.status == 429:
                logger.warning(f"Groq rate-limited — model:{model}")
                return None
            else:
                err = await resp.text()
                logger.error(f"Groq {resp.status} — model:{model} err:{err[:100]}")
                return None
    except Exception as e:
        logger.error(f"Groq exception model:{model} — {e}")
        return None


async def _try_openrouter(session: aiohttp.ClientSession, api_key: str, model: str, payload: dict) -> str | None:
    """Bitta OpenRouter key + model kombinatsiyasini sinab ko'radi."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://t.me/englishbot",
        "X-Title": "English Learning Bot"
    }
    try:
        async with session.post(
            OPENROUTER_URL,
            json={**payload, "model": model},
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=15)  # Reduced from 40s
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                logger.info(f"OpenRouter OK — key:{api_key[:20]}... model:{model}")
                return data["choices"][0]["message"]["content"].strip()
            elif resp.status in (429, 503):
                logger.warning(f"OpenRouter {resp.status} — key:{api_key[:20]}... model:{model}")
                return None
            else:
                err = await resp.text()
                logger.error(f"OpenRouter {resp.status} — model:{model} err:{err[:100]}")
                return None
    except Exception as e:
        logger.error(f"OpenRouter exception model:{model} — {e}")
        return None


async def ask_openrouter(
    user_message: str,
    system_prompt: str = "You are a helpful English teacher for Uzbek speakers. Answer in Uzbek.",
    model: str = None,
    max_tokens: int = 800,
    temperature: float = 0.7
) -> str | None:
    """AI javob: Z.ai (Node SDK) -> Groq -> OpenRouter. Hech biri ishlamasa None qaytaradi."""
    from bot.ai.zai_bridge import ask_ai

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    result = await ask_ai(user_message, system_prompt=system_prompt,
                          max_tokens=max_tokens, temperature=temperature)
    if result is not None:
        return result

    return None
