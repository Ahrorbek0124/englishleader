import aiosqlite
import logging
from bot.config import DB_PATH

logger = logging.getLogger(__name__)


async def init_db():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("PRAGMA journal_mode=WAL")

            await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id      INTEGER PRIMARY KEY,
                username     TEXT,
                first_name   TEXT,
                nickname     TEXT,
                lang         TEXT DEFAULT 'uz',
                level        TEXT DEFAULT 'A1',
                streak       INTEGER DEFAULT 0,
                last_active  TEXT,
                total_words  INTEGER DEFAULT 0,
                created_at   TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """)
            for col, defval in [("nickname", "NULL"), ("lang", "'uz'")]:
                try:
                    await db.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT DEFAULT {defval}")
                except Exception:
                    pass

            await db.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER,
                original     TEXT,
                translated   TEXT,
                mode         TEXT,
                created_at   TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS saved_words (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER,
                word         TEXT,
                translation  TEXT,
                next_review  TEXT,
                interval     INTEGER DEFAULT 1,
                ease         REAL DEFAULT 2.5,
                created_at   TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER,
                topic        TEXT,
                score        INTEGER,
                total        INTEGER,
                created_at   TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS user_topics (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER,
                topic_key    TEXT,
                topic_name   TEXT,
                learned_at   TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, topic_key)
            )
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS game_progress (
                user_id          INTEGER PRIMARY KEY,
                xp               INTEGER DEFAULT 0,
                completed_topics TEXT DEFAULT '[]',
                streak           INTEGER DEFAULT 0,
                last_played      TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """)

            await db.commit()
            logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")


async def get_db_connection():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def get_user_lang(user_id: int) -> str:
    db = await get_db_connection()
    try:
        cursor = await db.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row["lang"] if row and row["lang"] else "uz"
    except Exception:
        return "uz"
    finally:
        await db.close()


async def set_user_lang(user_id: int, lang: str):
    db = await get_db_connection()
    try:
        await db.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))
        await db.commit()
    finally:
        await db.close()


# ─── Game Progress CRUD ───────────────────────────────────────────────────
async def get_game_progress(user_id: int) -> dict:
    """Get game progress for a user. Returns dict with xp, completed_topics."""
    db = await get_db_connection()
    try:
        cursor = await db.execute(
            "SELECT xp, completed_topics, streak, last_played FROM game_progress WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            import json
            topics = json.loads(row["completed_topics"]) if row["completed_topics"] else []
            return {
                "xp": row["xp"] or 0,
                "completed_topics": topics,
                "streak": row["streak"] or 0,
                "last_played": row["last_played"] or "",
            }
        return {"xp": 0, "completed_topics": [], "streak": 0, "last_played": ""}
    except Exception:
        return {"xp": 0, "completed_topics": [], "streak": 0, "last_played": ""}
    finally:
        await db.close()


async def save_game_progress(user_id: int, xp: int, completed_topics: list) -> None:
    """Save game progress for a user."""
    import json
    db = await get_db_connection()
    try:
        topics_json = json.dumps(completed_topics)
        await db.execute(
            "INSERT INTO game_progress (user_id, xp, completed_topics, last_played) "
            "VALUES (?, ?, ?, datetime('now')) "
            "ON CONFLICT(user_id) DO UPDATE SET xp=?, completed_topics=?, last_played=datetime('now')",
            (user_id, xp, topics_json, xp, topics_json)
        )
        await db.commit()
    except Exception as e:
        logger.error(f"Error saving game progress: {e}")
    finally:
        await db.close()
