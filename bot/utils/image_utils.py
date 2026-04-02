import io
import logging
import textwrap
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


def _get_font(size: int = 18):
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _wrap_text(text: str, max_width: int, font, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        try:
            w = draw.textlength(test, font=font)
        except Exception:
            w = len(test) * 10
        if w <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def create_translated_image(
    original_bytes: bytes,
    original_text: str,
    translated_text: str,
    target_lang: str = "en"
) -> bytes:
    """
    Overlay a beautiful translation panel on the bottom of the image.
    Shows BOTH: original text (before translation) and translated text.
    """
    try:
        img = Image.open(io.BytesIO(original_bytes)).convert("RGB")
        img_w, img_h = img.size

        font_main  = _get_font(18)
        font_label = _get_font(13)
        font_orig  = _get_font(14)

        dummy     = Image.new("RGB", (img_w, 100))
        draw_d    = ImageDraw.Draw(dummy)
        orig_lines  = _wrap_text(original_text[:200], img_w - 24, font_orig, draw_d)
        trans_lines = _wrap_text(translated_text, img_w - 24, font_main, draw_d)

        line_h    = 24
        small_h   = 20
        padding   = 14
        sep_h     = 3
        label_h   = 22

        orig_block_h  = label_h + len(orig_lines) * small_h + 8
        trans_block_h = label_h + len(trans_lines) * line_h + 8
        panel_h = sep_h + orig_block_h + 6 + trans_block_h + padding * 2
        panel_h = max(panel_h, 100)

        new_h   = img_h + panel_h
        new_img = Image.new("RGB", (img_w, new_h), (12, 15, 30))
        new_img.paste(img, (0, 0))
        draw    = ImageDraw.Draw(new_img)

        # Panel background gradient effect (dark navy)
        draw.rectangle([0, img_h, img_w, new_h], fill=(14, 18, 36))

        # Top accent line
        draw.rectangle([0, img_h, img_w, img_h + sep_h], fill=(99, 102, 241))

        y = img_h + padding

        # ── Original text section ──────────────────────────────────────────
        draw.text((10, y), "🔍 Asl matn:", fill=(148, 163, 255), font=font_label)
        y += label_h
        for line in orig_lines:
            if y + small_h > new_h - 4: break
            draw.text((14, y), line, fill=(200, 210, 255), font=font_orig)
            y += small_h

        y += 8
        # Thin separator
        draw.rectangle([10, y, img_w - 10, y + 1], fill=(45, 50, 90))
        y += 7

        # ── Translated text section ────────────────────────────────────────
        draw.text((10, y), "✅ Tarjima:", fill=(52, 211, 153), font=font_label)
        y += label_h
        for line in trans_lines:
            if y + line_h > new_h - 4: break
            draw.text((14, y), line, fill=(255, 255, 255), font=font_main)
            y += line_h

        out = io.BytesIO()
        new_img.save(out, format="JPEG", quality=90)
        return out.getvalue()

    except Exception as e:
        logger.error(f"create_translated_image failed: {e}")
        return original_bytes


def draw_text_on_image(image_bytes: bytes, translations: list) -> bytes:
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        draw  = ImageDraw.Draw(image)
        font  = _get_font(16)
        for t in translations:
            box  = t.get("box", [10, 10, 200, 40])
            text = t.get("text", "")
            draw.rectangle(box, fill="white")
            draw.text((box[0] + 2, box[1] + 2), text, fill="black", font=font)
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=85)
        return output.getvalue()
    except Exception as e:
        raise RuntimeError(f"Failed to draw on image: {e}")
