import aiohttp
from typing import Optional
from bot.config import OCR_SPACE_API_KEY


async def process_ocr_space(image_bytes: bytes) -> tuple[Optional[str], str]:
    """
    Extract text using OCR.Space (text only, no bounding boxes).
    Returns (extracted_text, error_message).
    """
    if not OCR_SPACE_API_KEY:
        return None, "OCR.Space API key missing."

    url = "https://api.ocr.space/parse/image"
    form_data = aiohttp.FormData()
    form_data.add_field("apikey", OCR_SPACE_API_KEY)
    form_data.add_field("language", "eng")
    form_data.add_field("isOverlayRequired", "false")
    form_data.add_field("file", image_bytes, filename="image.jpg", content_type="image/jpeg")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=form_data, timeout=30) as response:
                if response.status != 200:
                    err = await response.text()
                    return None, f"OCR.Space Error {response.status}: {err}"

                res = await response.json()
                if res.get("IsErroredOnProcessing"):
                    return None, res.get("ErrorMessage", ["Unknown OCR.Space error"])[0]

                parsed = res.get("ParsedResults", [])
                if not parsed:
                    return None, "No parsed text blocks returned."

                text = parsed[0].get("ParsedText", "").strip()
                if not text:
                    return None, "No text found in image."

                return text, ""
    except Exception as e:
        return None, f"OCR.Space request failed: {e}"


async def process_ocr_with_overlay(image_bytes: bytes) -> tuple[Optional[str], list, str]:
    """
    Extract text WITH bounding box positions.
    Returns (full_text, word_boxes, error_message)
    word_boxes = [{"text": str, "left": int, "top": int, "width": int, "height": int}, ...]
    """
    if not OCR_SPACE_API_KEY:
        return None, [], "OCR.Space API key missing."

    url = "https://api.ocr.space/parse/image"
    form_data = aiohttp.FormData()
    form_data.add_field("apikey", OCR_SPACE_API_KEY)
    form_data.add_field("language", "eng")
    form_data.add_field("isOverlayRequired", "true")   # ← get bounding boxes
    form_data.add_field("file", image_bytes, filename="image.jpg", content_type="image/jpeg")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=form_data, timeout=30) as response:
                if response.status != 200:
                    err = await response.text()
                    return None, [], f"OCR.Space Error {response.status}: {err}"

                res = await response.json()
                if res.get("IsErroredOnProcessing"):
                    return None, [], res.get("ErrorMessage", ["Unknown error"])[0]

                parsed = res.get("ParsedResults", [])
                if not parsed:
                    return None, [], "No parsed results."

                full_text = parsed[0].get("ParsedText", "").strip()
                if not full_text:
                    return None, [], "No text found in image."

                # Extract word-level boxes
                overlay = parsed[0].get("TextOverlay", {})
                lines   = overlay.get("Lines", [])
                word_boxes = []
                for line in lines:
                    line_words = line.get("Words", [])
                    line_texts = [w["WordText"] for w in line_words if w.get("WordText")]
                    if not line_texts:
                        continue
                    # Group line as one box (use bounding box of first & last word)
                    if line_words:
                        first = line_words[0]
                        last  = line_words[-1]
                        x1 = first.get("Left", 0)
                        y1 = first.get("Top", 0)
                        x2 = last.get("Left", 0) + last.get("Width", 0)
                        y2 = first.get("Top", 0) + first.get("Height", 0)
                        word_boxes.append({
                            "text":   " ".join(line_texts),
                            "left":   x1,
                            "top":    y1,
                            "width":  x2 - x1,
                            "height": y2 - y1,
                        })

                return full_text, word_boxes, ""
    except Exception as e:
        return None, [], f"OCR.Space overlay request failed: {e}"
