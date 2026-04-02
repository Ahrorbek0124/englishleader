from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes
from bot.ai.openrouter import ask_openrouter
from bot.database.db import get_db_connection, get_user_lang

# ─── Scenario list — must match keyboards.get_roleplay_menu() EXACTLY ─────────
from bot.utils.keyboards import get_main_menu, get_roleplay_menu

# Extract scenarios from the keyboard builder to stay in sync
ROLEPLAY_SCENARIOS = [
    "🏨 Hotel check-in",         "✈️ Airport boarding gate",
    "🛒 Shopping at a store",    "🏥 Doctor's appointment",
    "🍽️ Restaurant ordering",    "💼 Job interview",
    "📞 Phone conversation",     "🚕 Taxi — directions",
    "🏦 At the bank",            "🎓 University enrollment",
    "🏫 Classroom situation",    "🚂 At the train station",
    "🛂 At customs / border",    "💊 At the pharmacy",
    "📮 At the post office",     "🏋️ At the gym",
]

async def handle_roleplay_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_msg = update.message.text
    chat_id = update.effective_chat.id
    lang = await get_user_lang(update.effective_user.id)
    
    # Check if this is the initial scenario selection
    if user_msg in ROLEPLAY_SCENARIOS:
        import re
        role = re.sub(r'^[\U0001F000-\U0001FFFF\U00002600-\U000027BF\U0001F300-\U0001F9FF]\s*', '', user_msg).strip()
        context.user_data['roleplay_scenario'] = role
        context.user_data['roleplay_history'] = []
        
        await update.message.reply_text(
            f"Siz '{role}' ssenariysini tanladingiz.\n\n"
            "Endi siz u bilan ingliz tilida gaplashasiz. "
            "Agar xatolar bo'lsa, /feedback orqali tahlilni olasiz. "
            "Suhbatni tugatish uchun /end ni bosing.\n\n"
            "Men boshlayman:",
            reply_markup=get_main_menu(lang)
        )
        
        # Initiate first AI message
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        sys_prompt = f"You are playing the role in a real English conversation: {role}. Start the conversation naturally in English. Keep it simple and realistic."
        reply = await ask_openrouter("Start the conversation", system_prompt=sys_prompt)
        
        if reply:
            context.user_data['roleplay_history'].append(f"AI: {reply}")
            await update.message.reply_text(reply)
        else:
            await update.message.reply_text("⚠️ Xatolik, bot javob qaytara olmadi.")
        return

    # If already in roleplay session
    if 'roleplay_scenario' not in context.user_data:
        await update.message.reply_text(
            "Iltimos, avval ssenariyni tanlang:",
            reply_markup=get_roleplay_menu(lang)
        )
        return

    role = context.user_data['roleplay_scenario']
    
    if user_msg == "/end" or user_msg == "/feedback":
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        
        # Compile history
        hst = "\n".join(context.user_data.get('roleplay_history', []))
        sys_prompt = f"You are an English teacher. Review this roleplay conversation about {role}. Analyze ALL user messages, list grammar mistakes with corrections in Uzbek."
        
        feedback = await ask_openrouter(hst, system_prompt=sys_prompt, max_tokens=1500)
        await update.message.reply_text(
            "Suhbat tugadi. Mana sizning xatolaringiz ustida tahlil:\n\n" + (feedback or "Xato topilmadi."),
            reply_markup=get_main_menu(lang)
        )
        
        # Reset state logic handled dynamically by User input later, but clear roleplay
        del context.user_data['roleplay_scenario']
        context.user_data['state'] = "main"
        return

    # Continue Conversation
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    context.user_data['roleplay_history'].append(f"USER: {user_msg}")
    hst = "\n".join(context.user_data['roleplay_history'])
    
    sys_prompt = f"You are playing the role in a real English conversation about {role}. Respond naturally in English to continue the conversation. Do not correct the user here."
    reply = await ask_openrouter(hst, system_prompt=sys_prompt)
    
    if reply:
        context.user_data['roleplay_history'].append(f"AI: {reply}")
        await update.message.reply_text(reply)
    else:
        await update.message.reply_text("⚠️ Xatolik, bot javob qaytara olmadi.")
