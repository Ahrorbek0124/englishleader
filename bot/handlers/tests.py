import json
import re
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from bot.ai.zai_bridge import ask_ai
from bot.database.db import get_db_connection, get_user_lang
from bot.services.i18n import get_trans
from bot.utils.keyboards import get_quiz_topic_keyboard, get_quiz_count_keyboard


def _extract_json(text: str) -> list | None:
    """Extract JSON array from AI response, handling various formats."""
    if not text:
        return None

    # Try direct parse
    try:
        data = json.loads(text.strip())
        if isinstance(data, list) and data:
            return data
    except (json.JSONDecodeError, ValueError):
        pass

    # Remove markdown code blocks
    cleaned = text.strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)

    # Try parse again
    try:
        data = json.loads(cleaned.strip())
        if isinstance(data, list) and data:
            return data
    except (json.JSONDecodeError, ValueError):
        pass

    # Find JSON array using regex
    match = re.search(r'\[\s*\{.*?\}\s*\]', cleaned, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            if isinstance(data, list) and data:
                return data
        except (json.JSONDecodeError, ValueError):
            pass

    # Try to find array even with nested braces
    depth = 0
    start = -1
    for i, ch in enumerate(cleaned):
        if ch == '[':
            if depth == 0:
                start = i
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0 and start >= 0:
                try:
                    data = json.loads(cleaned[start:i+1])
                    if isinstance(data, list) and data:
                        return data
                except (json.JSONDecodeError, ValueError):
                    pass

    return None


def _validate_question(q: dict) -> dict | None:
    """Validate a single question has required fields."""
    if not isinstance(q, dict):
        return None
    if "question" not in q or "options" not in q or "correct" not in q:
        return None
    if not isinstance(q["options"], list) or len(q["options"]) < 2:
        return None
    correct = q["correct"]
    if isinstance(correct, str):
        # Try to find index
        try:
            correct = q["options"].index(correct)
        except ValueError:
            try:
                correct = int(correct)
            except (ValueError, TypeError):
                return None
    if not isinstance(correct, int) or correct < 0 or correct >= len(q["options"]):
        return None
    return {
        "question": str(q["question"]).strip(),
        "options": [str(o).strip() for o in q["options"]],
        "correct": correct,
        "explanation": str(q.get("explanation", "")).strip(),
    }


# ─── Step 1: Show topic selection ───────────────────────────────────────────
async def show_test_menu(message, context: ContextTypes.DEFAULT_TYPE, lang: str = "uz") -> None:
    t = lambda k, **kw: get_trans(lang, k, **kw)
    context.user_data['quiz_step'] = 'choosing_topic'
    await message.reply_text(
        f"🧠 *{t('choose_topic')}*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown",
        reply_markup=get_quiz_topic_keyboard(lang)
    )


# ─── Step 2: Show count selection (after topic chosen) ──────────────────────
async def show_count_menu(message, context: ContextTypes.DEFAULT_TYPE, topic: str, lang: str = "uz") -> None:
    t = lambda k, **kw: get_trans(lang, k, **kw)
    context.user_data['quiz_step'] = 'choosing_count'
    context.user_data['pending_topic'] = topic
    await message.reply_text(
        f"📚 *Mavzu:* {topic}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{t('choose_count')}",
        parse_mode="Markdown",
        reply_markup=get_quiz_count_keyboard(lang)
    )


# ─── Step 3: Actually start quiz ────────────────────────────────────────────
async def start_quiz(message, context: ContextTypes.DEFAULT_TYPE,
                     topic: str, count: int = 5, lang: str = "uz") -> None:
    t = lambda k, **kw: get_trans(lang, k, **kw)

    loading_msg = await message.reply_text(
        f"⏳ *{t('quiz_creating', topic=topic, count=count)}*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔄 AI javob tayyorlayapti...",
        parse_mode="Markdown"
    )
    await context.bot.send_chat_action(chat_id=message.chat_id, action=ChatAction.TYPING)

    prompt = f"""Create {count} multiple choice English grammar questions about "{topic}".

IMPORTANT: Return ONLY a valid JSON array. No other text, no markdown, no explanation before or after.

Format:
[
  {{
    "question": "She ___ to the market yesterday.",
    "options": ["go", "went", "goes", "gone"],
    "correct": 1,
    "explanation": "Past Simple form of 'go' is 'went'."
  }}
]

Rules:
- "correct" must be the INDEX (0-3) of the correct option
- All 4 options must be unique
- Use ___ (triple underscore) for fill-in-the-blank questions
- Questions should be medium difficulty
- Include clear explanations
- Return ONLY the JSON array, nothing else"""

    res = await ask_ai("Generate the questions now.", system_prompt=prompt, max_tokens=3000, temperature=0.8)

    if not res:
        await loading_msg.edit_text(
            "❌ *AI javob bera olmadi*\n\n"
            "⚡ Birozdan so'ng qaytadan urinib ko'ring.\n"
            "Yoki boshqa mavzuni tanlang.",
            parse_mode="Markdown"
        )
        context.user_data.pop('quiz_step', None)
        context.user_data.pop('pending_topic', None)
        return

    # Parse JSON from response
    questions_raw = _extract_json(res)

    if not questions_raw:
        await loading_msg.edit_text(
            f"⚠️ *AI javob formati noto'g'ri*\n\n"
            f"Iltimos qaytadan urinib ko'ring.\n"
            f"Yoki boshqa mavzu tanlang.",
            parse_mode="Markdown"
        )
        context.user_data.pop('quiz_step', None)
        context.user_data.pop('pending_topic', None)
        return

    # Validate and clean questions
    questions = []
    for q in questions_raw:
        valid = _validate_question(q)
        if valid:
            questions.append(valid)

    if not questions:
        await loading_msg.edit_text(
            "❌ *Savollar formati noto'g'ri*\n\n"
            "Iltimos qaytadan urinib ko'ring.",
            parse_mode="Markdown"
        )
        context.user_data.pop('quiz_step', None)
        context.user_data.pop('pending_topic', None)
        return

    # Trim to requested count
    questions = questions[:count]

    try:
        await loading_msg.delete()
    except Exception:
        pass

    context.user_data['current_quiz']  = questions
    context.user_data['quiz_index']    = 0
    context.user_data['quiz_score']    = 0
    context.user_data['quiz_topic']    = topic
    context.user_data['quiz_count']    = len(questions)
    context.user_data['quiz_lang']     = lang
    context.user_data['quiz_step']     = 'in_progress'

    await send_next_question(message, context)


# ─── Send one question ───────────────────────────────────────────────────────
async def send_next_question(message, context: ContextTypes.DEFAULT_TYPE) -> None:
    q_data  = context.user_data.get('current_quiz', [])
    q_index = context.user_data.get('quiz_index', 0)
    lang    = context.user_data.get('quiz_lang', 'uz')

    if not q_data or q_index >= len(q_data):
        score = context.user_data.get('quiz_score', 0)
        total = len(q_data) if q_data else 0
        topic = context.user_data.get('quiz_topic', "Test")
        pct   = round(score / total * 100) if total else 0

        if pct >= 90:   emoji, comment = "🏆", "Zo'r! Mukammal natija!"
        elif pct >= 70: emoji, comment = "🌟", "Yaxshi! Davom eting!"
        elif pct >= 50: emoji, comment = "📈", "O'rtacha. Ko'proq mashq qiling!"
        else:           emoji, comment = "💪", "Kamroq bo'ldi. Qaytadan o'rganing!"

        t = lambda k, **kw: get_trans(lang, k, **kw)

        # Save to DB
        db = await get_db_connection()
        try:
            await db.execute(
                "INSERT INTO test_results (user_id, topic, score, total) VALUES (?, ?, ?, ?)",
                (message.chat_id, topic, score, total)
            )
            await db.commit()
        finally:
            await db.close()

        result_text = (
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{emoji} *Test Tugadi!*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📚 Mavzu: *{topic}*\n"
            f"📊 Natija: {score}/{total} ({pct}%)\n\n"
            f"{emoji} {comment}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )

        # Progress bar
        filled = round(pct / 100 * 15)
        bar = "█" * filled + "░" * (15 - filled)
        result_text += f"\n📈 Progress: [{bar}] {pct}%\n"

        await message.reply_text(result_text, parse_mode="Markdown")

        # Clean state
        for key in ['current_quiz', 'quiz_index', 'quiz_score', 'quiz_topic',
                    'quiz_count', 'quiz_lang', 'quiz_step', 'pending_topic']:
            context.user_data.pop(key, None)
        return

    q_item  = q_data[q_index]
    options = q_item.get('options', [])
    total   = len(q_data)

    # Progress dots
    dots = ""
    for i in range(total):
        if i < q_index:
            dots += "🟢 "
        elif i == q_index:
            dots += "🔴 "
        else:
            dots += "⚪ "

    # Make blanks more visible in the question
    question_text = q_item['question']
    question_text = question_text.replace(" __ ", " \u2756\u2756\u2756 ")
    question_text = question_text.replace("__", " \u2756\u2756\u2756 ")
    
    text = (
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"❓ *Savol {q_index + 1}/{total}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{dots}\n\n"
        f"📝 {question_text}\n\n"
        f"👇 *Javobni tanlang:*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )

    labels  = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
    buttons = []
    for i, opt in enumerate(options):
        label = labels[i] if i < len(labels) else f"{i+1}."
        buttons.append([InlineKeyboardButton(f"{label}  {opt}", callback_data=f"ans_{i}")])

    await message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))


# ─── Handle answer callback ──────────────────────────────────────────────────
async def handle_quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data

    # Handle topic selection
    if data.startswith("qtopic_"):
        lang  = await get_user_lang(query.from_user.id)
        topic = data.replace("qtopic_", "")
        if topic == "OTHER":
            context.user_data['quiz_step'] = 'awaiting_custom_topic'
            t = lambda k: get_trans(lang, k)
            await query.message.reply_text(f"✏️ {t('other_topic')}")
            return
        await show_count_menu(query.message, context, topic, lang)
        return

    # Handle count selection
    if data.startswith("qcount_"):
        lang  = await get_user_lang(query.from_user.id)
        count = int(data.replace("qcount_", ""))
        topic = context.user_data.get('pending_topic', 'General Grammar')
        await start_quiz(query.message, context, topic=topic, count=count, lang=lang)
        return

    # Handle answer
    if not data.startswith("ans_"):
        return

    ans_index = int(data.split("_")[1])
    q_data    = context.user_data.get('current_quiz', [])
    q_index   = context.user_data.get('quiz_index', 0)
    lang      = context.user_data.get('quiz_lang', 'uz')

    if q_index >= len(q_data):
        return

    q_item      = q_data[q_index]
    correct_idx = q_item.get('correct', 0)
    explanation = q_item.get('explanation', '')
    options     = q_item.get('options', [])

    if ans_index == correct_idx:
        context.user_data['quiz_score'] = context.user_data.get('quiz_score', 0) + 1
        msg = (
            f"✅ *To'g'ri!* 🎉\n\n"
            f"💡 {explanation}"
        )
    else:
        correct_text = options[correct_idx] if correct_idx < len(options) else "?"
        msg = (
            f"❌ *Noto'g'ri.*\n\n"
            f"✅ To'g'ri javob: *{correct_text}*\n\n"
            f"💡 {explanation}"
        )

    await query.message.reply_text(msg, parse_mode="Markdown")

    context.user_data['quiz_index'] = q_index + 1
    await send_next_question(query.message, context)
