import aiohttp
from typing import Optional

from bot.config import NINJAS_API_KEY

async def process_ocr_ninjas(image_bytes: bytes) -> tuple[Optional[str], str]:
    """
    Extract text using API Ninjas OCR wrapper as fallback.
    Returns (extracted_text, error_message).
    """
    if not NINJAS_API_KEY:
        return None, "API Ninjas API key missing."

    url = 'https://api.api-ninjas.com/v1/imagetotext'
    headers = {'X-Api-Key': NINJAS_API_KEY}

    form_data = aiohttp.FormData()
    form_data.add_field(
        "image",
        image_bytes,
        filename="image.jpg",
        content_type="image/jpeg"
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=form_data, timeout=30) as response:
                if response.status != 200:
                    err = await response.text()
                    return None, f"API Ninjas OCR Error {response.status}: {err}"

                res = await response.json()
                # Returns an array of text dictionaries -> [{"text": "Hello"}, {"text": "World"}]
                if not isinstance(res, list):
                    return None, "Unexpected response format from API Ninjas."

                texts = [item.get("text", "") for item in res if item.get("text")]
                full_text = " ".join(texts).strip()
                
                if not full_text:
                    return None, "No recognizable text retrieved from API Ninjas."

                return full_text, ""
    except Exception as e:
        return None, f"API Ninjas request failed: {e}"
