import logging
import traceback
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from telegram.ext import JobQueue
from bot.config import BOT_TOKEN
from bot.database.db import init_db
from bot.handlers.commands import (
    start_command, stats_command, help_command,
    vocabulary_command, history_command, settings_command
)
from bot.handlers.translate import handle_text
from bot.handlers.voice import handle_voice
from bot.handlers.photo import handle_photo
from bot.handlers.document import handle_document
from bot.handlers.callbacks import handle_callbacks
from bot.handlers.tenses import handle_tense_callback
from bot.handlers.tests import handle_quiz_callback
from bot.handlers.vocabulary import setup_vocabulary_jobs
from bot.handlers.games import handle_game_callback
from bot.handlers.video_lessons import handle_video_callback

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def error_handler(update: Update, context) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ Texnik muammo yuz berdi. Qaytadan urinib ko'ring yoki /start bosing."
            )
    except Exception:
        pass


def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is missing!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).job_queue(JobQueue()).build()

    async def post_init(application):
        logger.info("Initializing database...")
        await init_db()
        setup_vocabulary_jobs(application)

    app.post_init = post_init
    app.add_error_handler(error_handler)

    # ── Commands ──────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start",      start_command))
    app.add_handler(CommandHandler("stats",      stats_command))
    app.add_handler(CommandHandler("help",       help_command))
    app.add_handler(CommandHandler("vocabulary", vocabulary_command))
    app.add_handler(CommandHandler("history",    history_command))
    app.add_handler(CommandHandler("settings",   settings_command))

    # ── Media ─────────────────────────────────────────────────────────────
    app.add_handler(MessageHandler(filters.VOICE,        handle_voice))
    app.add_handler(MessageHandler(filters.PHOTO,        handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # ── Unified callback router ───────────────────────────────────────────
    async def master_callback(update: Update, context):
        data = update.callback_query.data

        # Game callbacks
        if data.startswith("game_"):
            await handle_game_callback(update, context)
            return

        # Video callbacks
        if data.startswith("vidcat_") or data.startswith("vidplay_") or data.startswith("vid_"):
            await handle_video_callback(update, context)
            return

        if data.startswith("tense_") and not data.startswith("tense_quiz"):
            await handle_tense_callback(update, context)
        elif data.startswith("ans_") or data.startswith("qtopic_") or data.startswith("qcount_"):
            await handle_quiz_callback(update, context)
        elif data.startswith("quiz_tense_"):
            await handle_callbacks(update, context)
        else:
            await handle_callbacks(update, context)

    app.add_handler(CallbackQueryHandler(master_callback))

    # ── Text (must be last) ───────────────────────────────────────────────
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("🤖 EnglishLeader Bot v2.0 GodMode is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.critical(f"Bot crashed on startup: {e}")
        traceback.print_exc()
