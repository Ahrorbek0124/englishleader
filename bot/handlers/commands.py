from telegram import Update
from telegram.ext import ContextTypes
from bot.utils.keyboards import get_main_menu, get_language_selection_keyboard, get_settings_keyboard, LANG_INFO
from bot.database.db import get_db_connection, get_user_lang, set_user_lang


async def _get_user_name(user_id: int) -> str:
    """Get user's display name: nickname > first_name from DB."""
    db = await get_db_connection()
    try:
        cursor = await db.execute(
            "SELECT nickname, first_name FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            return row["nickname"] or row["first_name"] or "Friend"
    except Exception:
        pass
    finally:
        await db.close()
    return "Friend"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    # Check if user already has a name and language set (returning user)
    db = await get_db_connection()
    try:
        cursor = await db.execute(
            "SELECT nickname, lang FROM users WHERE user_id = ?", (user.id,)
        )
        row = await cursor.fetchone()
    finally:
        await db.close()

    # Register/update user in DB
    db = await get_db_connection()
    try:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, last_active) "
            "VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            (user.id, user.username, user.first_name)
        )
        await db.execute(
            "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
            (user.id,)
        )
        await db.commit()
    finally:
        await db.close()

    # If user already has both a name and a language, show welcome directly
    if row and row["lang"] and row["lang"] != "uz" and row.get("nickname"):
        from bot.services.i18n import get_trans
        lang = row["lang"]
        name = row["nickname"]
        welcome = get_trans(lang, "welcome", name=name)
        context.user_data['state'] = "main"
        await update.message.reply_text(welcome, reply_markup=get_main_menu(lang))
        return

    # New user flow: Step 1 - Ask for name
    context.user_data['state'] = "awaiting_name"
    context.user_data['setup_step'] = "name"

    await update.message.reply_text(
        "👋 *Welcome to EnglishLeader Bot!*\n\n"
        "🤖 I'm your AI-powered English learning assistant.\n"
        "📚 I support 30+ languages for translation, grammar lessons, tests, and more!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📝 *Let's get started!*\n\n"
        "💡 Please enter your name so I can personalize your experience:",
        parse_mode="Markdown"
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from bot.handlers.status import show_status
    await show_status(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    lang = await get_user_lang(user_id)
    from bot.services.i18n import get_trans
    t = lambda k, **kw: get_trans(lang, k, **kw)
    await update.message.reply_text(
        t("about_text"),
        parse_mode="Markdown"
    )


async def vocabulary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from bot.handlers.vocabulary import start_vocabulary
    await start_vocabulary(update, context)


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from bot.handlers.callbacks import show_history
    await show_history(update, context)


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    lang = await get_user_lang(user_id)
    from bot.services.i18n import get_trans
    t = lambda k, **kw: get_trans(lang, k, **kw)
    await update.message.reply_text(
        f"*{t('settings_title')}*\n\n{t('settings_text')}",
        parse_mode="Markdown",
        reply_markup=get_settings_keyboard(lang)
    )
