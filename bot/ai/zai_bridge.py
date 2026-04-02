"""
Z.ai local bridge — Groq (multi-key) + OpenRouter fallback bilan.
Bot ichidan chaqiriladi, tashqi proxy kerak emas.
"""
import subprocess, json, logging, os, re

logger = logging.getLogger(__name__)

# ── Z.ai: Node.js SDK orqali ────────────────────────────────────────────────
_ZAI_JS = '''
const ZAI = require("z-ai-web-dev-sdk").default;
async function main() {
  const zai = await ZAI.create();
  const payload = JSON.parse(process.argv[2]);
  const result = await zai.chat.completions.create(payload);
  process.stdout.write(JSON.stringify(result));
}
main().catch(e => { process.stderr.write(e.message); process.exit(1); });
'''


async def _run_node(script: str, arg: str = "", timeout: int = 45) -> subprocess.CompletedProcess | None:
    """Node.js skriptini subprocess sifatida ishga tushiradi."""
    js_file = "/tmp/_zai_bridge.js"
    try:
        with open(js_file, "w") as f:
            f.write(script)
        proc = subprocess.run(
            ["node", js_file, arg],
            capture_output=True, text=True, timeout=timeout,
            cwd="/home/z/my-project",
            env={**os.environ, "NODE_PATH": "/home/z/my-project/node_modules"}
        )
        if proc.returncode != 0:
            logger.error(f"Node.js error: {proc.stderr[:300]}")
            return None
        return proc
    except subprocess.TimeoutExpired:
        logger.error(f"Node.js timeout ({timeout}s)")
        return None
    except Exception as e:
        logger.error(f"Node.js run error: {e}")
        return None


async def _try_zai(messages, max_tokens=2000, temperature=0.7) -> str | None:
    """Z.ai ni Node.js SDK orqali chaqiradi (proxy kerak emas)."""
    # Skip Z.ai bridge on cloud (no Node.js)
    if not os.path.exists("/home/z/my-project/node_modules/z-ai-web-dev-sdk"):
        return None
    try:
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        proc = await _run_node(_ZAI_JS, json.dumps(payload), timeout=60)
        if proc and proc.stdout:
            data = json.loads(proc.stdout)
            content = data["choices"][0]["message"]["content"].strip()
            logger.info(f"Z.ai OK (model: {data.get('model','?')})")
            return content
    except Exception as e:
        logger.error(f"Z.ai Node.js error: {e}")
    return None


# ── Groq fallback (multi-key) ───────────────────────────────────────────────
async def _try_groq(messages, max_tokens=2000, temperature=0.7) -> str | None:
    import aiohttp
    from bot.config import GROQ_API_KEYS

    models = [
        "llama-3.3-70b-versatile",
        "llama3-70b-8192",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ]
    async with aiohttp.ClientSession() as session:
        for api_key in GROQ_API_KEYS:
            for model in models:
                try:
                    async with session.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        json={
                            "model": model,
                            "messages": messages,
                            "max_tokens": max_tokens,
                            "temperature": temperature,
                        },
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        },
                        timeout=aiohttp.ClientTimeout(total=20),
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            logger.info(f"Groq OK: {model} (key: ...{api_key[-6:]})")
                            return data["choices"][0]["message"]["content"].strip()
                        elif resp.status == 429:
                            logger.warning(f"Groq rate limited: {model}")
                            continue
                        elif resp.status == 401:
                            logger.error(f"Groq auth failed for key ...{api_key[-6:]}")
                            break  # skip this key entirely
                        else:
                            err = await resp.text()
                            logger.error(f"Groq {resp.status} model:{model} err:{err[:100]}")
                            continue
                except Exception as e:
                    logger.error(f"Groq error {model}: {e}")
                    continue
    return None


# ── OpenRouter fallback ────────────────────────────────────────────────────
async def _try_openrouter(messages, max_tokens=2000, temperature=0.7) -> str | None:
    import aiohttp
    from bot.config import OPENROUTER_API_KEYS

    models = [
        "google/gemma-3-27b-it:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "mistralai/mistral-small-3.1-24b-instruct:free",
        "deepseek/deepseek-r1-distill-llama-70b:free",
    ]

    async with aiohttp.ClientSession() as session:
        for model in models:
            for key in OPENROUTER_API_KEYS:
                try:
                    async with session.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        json={"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature},
                        headers={
                            "Authorization": f"Bearer {key}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": "https://t.me/englishleaderbot",
                            "X-Title": "EnglishLeader Bot v2.0",
                        },
                        timeout=aiohttp.ClientTimeout(total=15),
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            logger.info(f"OpenRouter OK: {model}")
                            return data["choices"][0]["message"]["content"].strip()
                        elif resp.status in (429, 503):
                            continue
                except Exception as e:
                    logger.error(f"OpenRouter error: {e}")
                    continue
    return None


# ── Main function ──────────────────────────────────────────────────────────
async def ask_ai(
    user_message: str,
    system_prompt: str = "You are a helpful English teacher. Answer clearly with examples. Use emojis.",
    max_tokens: int = 2000,
    temperature: float = 0.7,
) -> str:
    """AI javob beradi: Z.ai -> Groq -> OpenRouter."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    # 1. Z.ai (eng yaxshi, bepul, local)
    result = await _try_zai(messages, max_tokens, temperature)
    if result:
        return result

    # 2. Groq (tezkor, bepul, multi-key)
    logger.warning("Z.ai failed, trying Groq...")
    result = await _try_groq(messages, max_tokens, temperature)
    if result:
        return result

    # 3. OpenRouter (so'nggi choro)
    logger.warning("Groq failed, trying OpenRouter...")
    result = await _try_openrouter(messages, max_tokens, temperature)
    if result:
        return result

    logger.error("ALL AI providers failed.")
    return None
