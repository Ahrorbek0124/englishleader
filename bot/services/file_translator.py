"""
file_translator.py
Extract text from uploaded documents (.txt, .docx, .pdf) for translation.

Dependencies:
  - python-docx  (for .docx)
  - PyPDF2       (for .pdf)
"""
from __future__ import annotations

from typing import Tuple

MAX_TEXT_LENGTH = 3000  # Characters sent to translator (Telegram limit ~4096)


def extract_text_from_bytes(file_bytes: bytes, filename: str) -> Tuple[str, bool]:
    """
    Extract readable text from file bytes.

    Returns:
        (extracted_text_or_error, success: bool)
    """
    lower = filename.lower()

    # ── Plain text ─────────────────────────────────────────────
    if lower.endswith(".txt"):
        try:
            text = file_bytes.decode("utf-8", errors="replace").strip()
            return _truncate(text), bool(text)
        except Exception as e:
            return f"❌ TXT o'qishda xatolik: {e}", False

    # ── Word document ───────────────────────────────────────────
    elif lower.endswith(".docx"):
        try:
            import io
            from docx import Document  # type: ignore
            doc = Document(io.BytesIO(file_bytes))
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            if not text:
                return "❌ Fayl bo'sh yoki matn topilmadi.", False
            return _truncate(text), True
        except ImportError:
            return "❌ python-docx o'rnatilmagan. `pip install python-docx`", False
        except Exception as e:
            return f"❌ DOCX o'qishda xatolik: {e}", False

    # ── PDF document ────────────────────────────────────────────
    elif lower.endswith(".pdf"):
        try:
            import io
            import PyPDF2  # type: ignore
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            pages = []
            for page in reader.pages:
                pages.append(page.extract_text() or "")
            text = "\n".join(pages).strip()
            if not text:
                return "❌ PDF faylda matn topilmadi (skaner qilingan rasm bo'lishi mumkin).", False
            return _truncate(text), True
        except ImportError:
            return "❌ PyPDF2 o'rnatilmagan. `pip install PyPDF2`", False
        except Exception as e:
            return f"❌ PDF o'qishda xatolik: {e}", False

    # ── Unsupported format ──────────────────────────────────────
    else:
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "?"
        return (
            f"❌ `.{ext}` fayl formati qo'llab-quvvatlanmaydi.\n"
            "Qo'llab-quvvatlanadigan formatlar: `.txt`, `.docx`, `.pdf`",
            False,
        )


def _truncate(text: str) -> str:
    if len(text) <= MAX_TEXT_LENGTH:
        return text
    return text[:MAX_TEXT_LENGTH] + f"\n\n... (Fayl juda katta, faqat birinchi {MAX_TEXT_LENGTH} belgi tarjima qilindi)"
