import aiohttp
import logging
from bot.config import OCR_SPACE_API_KEY, NINJAS_API_KEY
from bot.ai.openrouter import ask_openrouter
import base64

logger = logging.getLogger(__name__)

async def ocr_space(image_bytes: bytes) -> tuple[str | None, str | None]:
    if not OCR_SPACE_API_KEY:
        return None, "OCR Space API Key missing"
        
    url = "https://api.ocr.space/parse/image"
    payload = {'apikey': OCR_SPACE_API_KEY, 'language': 'eng'}
    form = aiohttp.FormData(payload)
    form.add_field('file', image_bytes, filename='image.jpg', content_type='image/jpeg')
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=form, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    if not data.get("IsErroredOnProcessing"):
                        parsed_results = data.get("ParsedResults", [])
                        if parsed_results:
                            return parsed_results[0].get("ParsedText"), None
                return None, "OCR Space parsing failed or returned error"
    except Exception as e:
        logger.error(f"OCR Space failed: {e}")
        return None, str(e)

async def ninjas_ocr(image_bytes: bytes) -> tuple[str | None, str | None]:
    if not NINJAS_API_KEY:
        return None, "Ninjas API Key missing"
        
    url = 'https://api.api-ninjas.com/v1/imagetotext'
    headers = {'X-Api-Key': NINJAS_API_KEY}
    form = aiohttp.FormData()
    form.add_field('image', image_bytes, filename='image.jpg', content_type='image/jpeg')
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=form, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        text = " ".join([item.get("text", "") for item in data])
                        return text, None
                return None, "Ninjas OCR returned empty or err"
    except Exception as e:
        logger.error(f"Ninjas OCR failed: {e}")
        return None, str(e)

async def process_image_ocr(image_bytes: bytes) -> tuple[str, bool]:
    """Extract text from image using OCR services, with AI vision fallback."""
    # Try OCR Space first
    text, err = await ocr_space(image_bytes)
    if text and text.strip():
        return text.strip(), True
    
    # Try Ninjas OCR
    text, err = await ninjas_ocr(image_bytes)
    if text and text.strip():
        return text.strip(), True
    
    # AI Vision fallback using Groq
    try:
        import json
        import base64 as _base64
        from bot.config import GROQ_API_KEYS
        import aiohttp
        
        b64_image = _base64.b64encode(image_bytes).decode('utf-8')
        
        for api_key in GROQ_API_KEYS:
            if not api_key:
                continue
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama-3.2-90b-vision-preview",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Extract ALL text from this image exactly as written. Return only the extracted text, nothing else. If there is no text, say 'No text found'."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{b64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.1
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=payload, timeout=30) as response:
                        if response.status == 200:
                            data = await response.json()
                            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                            if content and content.strip() and "No text found" not in content:
                                return content.strip(), True
            except Exception as e:
                logger.error(f"Groq vision failed with key: {e}")
                continue
        
        return "⚠️ Rasmdan matnni o'qib bo'lmadi. Iltimos matni aniqroq bo'lgan rasm yuboring.", False
    except Exception as e:
        logger.error(f"AI vision fallback failed: {e}")
        return "⚠️ Texnik muammo yuz berdi. Birozdan so'ng qaytadan urinib ko'ring.", False
