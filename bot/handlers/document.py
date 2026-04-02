import io
import PyPDF2
from docx import Document
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from bot.services.translator_service import translate_text, detect_language
from bot.utils.keyboards import get_audio_button
from bot.database.db import get_db_connection

def extract_text_from_bytes(file_bytes: bytes, filename: str) -> tuple[str, bool]:
    text = ""
    try:
        if filename.endswith(".txt"):
            text = file_bytes.decode('utf-8')
        elif filename.endswith(".docx"):
            doc = Document(io.BytesIO(file_bytes))
            text = "\n".join([para.text for para in doc.paragraphs])
        elif filename.endswith(".pdf"):
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        else:
            return "Faqat .txt, .docx, .pdf fayllar qo'llab-quvvatlanadi.", False
        
        if not text.strip():
            return "Fayl ichidan matn topilmadi.", False
        return text.strip(), True
    except Exception as e:
        return f"Faylni o'qishda xatolik: {e}", False

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.document: return
    chat_id = update.effective_chat.id
    
    await update.message.reply_text("⏳ Fayldagi matn o'qilmoqda...")
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    # Download
    doc = update.message.document
    doc_file = await context.bot.get_file(doc.file_id)
    doc_bytes = bytes(await doc_file.download_as_bytearray())

    # Extract
    extracted, ok = extract_text_from_bytes(doc_bytes, doc.file_name or "unknown.txt")
    if not ok:
        await update.message.reply_text(extracted)
        return

    # Translate in chunks of 1000
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    detected_lang = detect_language(extracted[:500])
    target = "uz" if detected_lang.startswith("en") else "en"
    
    chunks = [extracted[i:i+1000] for i in range(0, len(extracted), 1000)]
    translated_pieces = []
    
    for c in chunks:
        translated_pieces.append(await translate_text(c, source="auto", target=target))
        
    full_translation = "\n".join(translated_pieces)

    # Save to history (only save first chunk to prevent db bloat if it's huge)
    db = await get_db_connection()
    try:
        await db.execute(
            "INSERT INTO history (user_id, original, translated, mode) VALUES (?, ?, ?, ?)",
            (chat_id, extracted[:1000], full_translation[:1000], "file")
        )
        await db.commit()
        cursor = await db.execute("SELECT last_insert_rowid()")
        last_id = (await cursor.fetchone())[0]
    finally:
        await db.close()

    # Reassemble and send as text file
    out_bio = io.BytesIO(full_translation.encode('utf-8'))
    out_bio.name = f"translated_{target}_{doc.file_name or 'document'}.txt"
    
    await context.bot.send_document(
        chat_id=chat_id, 
        document=out_bio, 
        caption=f"✅ Tarjima qilingan fayl ({len(full_translation)} belgi).",
        reply_markup=get_audio_button(str(last_id))
    )
