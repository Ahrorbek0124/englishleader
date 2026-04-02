from telegram import Update
from telegram.ext import ContextTypes
import json
import logging
import datetime
import re

from bot.ai.openrouter import ask_openrouter
from bot.database.db import get_db_connection

logger = logging.getLogger(__name__)

def escape_md2(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    special_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(r'([' + re.escape(special_chars) + r'])', r'\\\1', str(text))

async def start_vocabulary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    db = await get_db_connection()
    try:
        cursor = await db.execute(
            "SELECT word, translation FROM saved_words WHERE user_id = ? AND next_review <= date('now') ORDER BY RANDOM() LIMIT 5",
            (chat_id,)
        )
        words = await cursor.fetchall()
    finally:
        await db.close()

    if not words:
        db = await get_db_connection()
        try:
            cursor = await db.execute(
                "SELECT word, translation FROM saved_words WHERE user_id = ? ORDER BY RANDOM() LIMIT 5",
                (chat_id,)
            )
            words = await cursor.fetchall()
        finally:
            await db.close()

        if not words:
            await update.message.reply_text(
                "📚 Sizda hozircha saqlangan so'zlar yo'q. Tarjimon orqali yangi so'zlarni saqlang!"
            )
            return

    # Build flashcards using MarkdownV2 with properly escaped text
    msg = "📝 *Flashcards \\(bugungi so'zlar\\):*\n\n"
    for w in words:
        word_esc = escape_md2(w['word'])
        trans_esc = escape_md2(w['translation'])
        msg += f"🇬🇧 {word_esc} — 🇺🇿 ||{trans_esc}||\n"
    
    msg += "\n\n_Yashirin matnni ko'rish uchun ustiga bosing_"
    
    try:
        await update.message.reply_text(msg, parse_mode="MarkdownV2")
    except Exception as e:
        # Fallback: plain text if markdown fails
        logger.error(f"MarkdownV2 failed, sending plain text: {e}")
        plain_msg = "📝 Flashcards (bugungi so'zlar):\n\n"
        for w in words:
            plain_msg += f"🇬🇧 {w['word']} — 🇺🇿 {w['translation']}\n"
        await update.message.reply_text(plain_msg)

async def word_of_the_day_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    prompt = """
    Generate an English Word of the Day in this exact JSON format:
    {
      "word": "serendipity",
      "pronunciation": "/ˌserənˈdipɪti/",
      "part_of_speech": "noun",
      "meaning_english": "the occurrence of events by chance in a happy or beneficial way",
      "meaning_uzbek": "tasodifiy baxtli kashfiyot",
      "examples": [
        {"en": "Finding that job was pure serendipity.", "uz": "O'sha ishni topish sof tasodif edi."},
        {"en": "Their meeting was a beautiful serendipity.", "uz": "Ularning uchrashishi chiroyli tasodif edi."}
      ],
      "synonyms": ["luck", "coincidence", "fortune"],
      "memory_tip": "Serendip is the old name for Sri Lanka. A fairy tale about lucky princes from there gave us this word."
    }
    Return ONLY valid JSON, nothing else.
    """
    
    res = await ask_openrouter("Generate Word of the Day", system_prompt=prompt)
    if not res:
        return
    
    try:
        if res.startswith("```json"):
            res = res[7:-3]
        elif res.startswith("```"):
            res = res[3:-3]
        data = json.loads(res.strip())
        
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        msg = (
            f"🌟 Word of the Day — {date_str}\n\n"
            f"📝 Word: {data['word'].upper()}\n"
            f"🔤 {data['pronunciation']} ({data['part_of_speech']})\n\n"
            f"🇬🇧 Meaning: {data['meaning_english']}\n"
            f"🇺🇿 O'zbekcha: {data['meaning_uzbek']}\n\n"
            f"💬 Examples:\n"
        )
        for ex in data['examples']:
            msg += f"• {ex['en']}\n  ({ex['uz']})\n"
        
        msg += f"\n🔗 Synonyms: {', '.join(data['synonyms'])}\n"
        msg += f"💡 Memory tip: {data['memory_tip']}\n"
        
        db = await get_db_connection()
        try:
            cursor = await db.execute("SELECT user_id FROM users")
            users = await cursor.fetchall()
            for u in users:
                try:
                    await context.bot.send_message(chat_id=u['user_id'], text=msg)
                except Exception:
                    pass
        finally:
            await db.close()
    except Exception as e:
        logger.error(f"Word of the Day processing failed: {e}")

def setup_vocabulary_jobs(application):
    import pytz
    tz = pytz.timezone("Asia/Tashkent")
    application.job_queue.run_daily(
        word_of_the_day_job,
        time=datetime.time(hour=9, minute=0, tzinfo=tz)
    )
