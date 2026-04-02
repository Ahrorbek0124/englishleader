import io
import logging
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from bot.database.db import get_db_connection, get_user_lang
from bot.services.i18n import get_trans
from bot.utils.keyboards import get_status_keyboard

logger = logging.getLogger(__name__)

# All available topics (for "pending" list)
ALL_TOPICS = [
    "Articles", "Prepositions", "Modal Verbs", "Conditionals",
    "Passive Voice", "Reported Speech", "Gerunds & Infinitives",
    "Comparatives", "Phrasal Verbs", "Idioms", "Tenses Overview",
    "Word Order", "Present Simple", "Present Continuous", "Present Perfect",
    "Past Simple", "Past Continuous", "Past Perfect", "Future Simple",
    "Be Going To", "Future Continuous", "Future Perfect",
]


def _fuzzy_match(a: str, b: str, threshold: float = 0.75) -> bool:
    """Case-insensitive fuzzy match between two strings."""
    a_low = a.strip().lower()
    b_low = b.strip().lower()
    if a_low == b_low:
        return True
    return SequenceMatcher(None, a_low, b_low).ratio() >= threshold


def _topic_is_learned(topic: str, learned_keys: set[str]) -> bool:
    """Check if a topic is in the learned set using case-insensitive and fuzzy matching."""
    topic_lower = topic.strip().lower()
    for lk in learned_keys:
        lk_lower = lk.strip().lower()
        if lk_lower == topic_lower:
            return True
        # Check if the learned key is contained in the topic or vice versa
        if lk_lower in topic_lower or topic_lower in lk_lower:
            return True
        if SequenceMatcher(None, lk_lower, topic_lower).ratio() >= 0.7:
            return True
    return False


def _make_progress_bar(pct: int, width: int = 15) -> str:
    filled = round(pct / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {pct}%"


def _make_ascii_chart(scores: list[tuple], width: int = 25) -> str:
    """Create a simple ASCII bar chart from (date, score_pct) pairs."""
    if not scores:
        return "📊 Ma'lumot yo'q"
    
    lines = []
    max_val = 100
    bar_h = 8
    
    # Show last 7 entries
    recent = scores[-7:]
    
    chart = []
    for label, pct in recent:
        bar_len = round(pct / max_val * 20)
        bar = "▓" * bar_len + "░" * (20 - bar_len)
        short_label = label[-5:] if len(label) > 5 else label  # last 5 chars of date
        chart.append(f"{short_label} │{bar}│ {pct}%")
    
    return "\n".join(chart)


async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id
    lang = await get_user_lang(user_id)
    t = lambda k, **kw: get_trans(lang, k, **kw)

    db = await get_db_connection()
    try:
        # User info
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()

        # Test results for graph
        cursor2 = await db.execute(
            "SELECT topic, score, total, created_at FROM test_results "
            "WHERE user_id = ? ORDER BY created_at ASC LIMIT 30",
            (user_id,)
        )
        tests = await cursor2.fetchall()

        # Saved words count
        wc = await db.execute("SELECT COUNT(*) as c FROM saved_words WHERE user_id = ?", (user_id,))
        words_count = (await wc.fetchone())["c"]

        # Learned topics count
        lc = await db.execute("SELECT COUNT(*) as c FROM user_topics WHERE user_id = ?", (user_id,))
        learned_count = (await lc.fetchone())["c"]

        # Today's tests
        today = datetime.now().strftime("%Y-%m-%d")
        tc = await db.execute(
            "SELECT score, total FROM test_results WHERE user_id = ? AND created_at LIKE ?",
            (user_id, f"{today}%")
        )
        today_tests = await tc.fetchall()
    finally:
        await db.close()

    total_tests = len(tests)
    name = row["nickname"] or row["first_name"] if row else user.first_name
    level = row["level"] if row else "A1"
    member_since = str(row["created_at"] or "").split()[0] if row else "?"

    # Overall score %
    if tests:
        all_pcts = [round(r["score"] / r["total"] * 100) if r["total"] else 0 for r in tests]
        overall_pct = round(sum(all_pcts) / len(all_pcts))
    else:
        overall_pct = 0

    # Today's score %
    if today_tests:
        today_pcts = [round(r["score"] / r["total"] * 100) if r["total"] else 0 for r in today_tests]
        today_pct = round(sum(today_pcts) / len(today_pcts))
    else:
        today_pct = 0

    # Learning speed: tests per day since first test
    if tests and len(tests) >= 2:
        first_date = datetime.fromisoformat(str(tests[0]["created_at"]).split()[0])
        days_active = max(1, (datetime.now() - first_date).days)
        tests_per_day = round(total_tests / days_active, 1)
    else:
        tests_per_day = 0

    # Level emoji
    level_emojis = {"A1": "🌱", "A2": "🌿", "B1": "🌳", "B2": "🌲", "C1": "⭐", "C2": "🏆"}
    level_emoji = level_emojis.get(level, "📚")

    # Build ASCII progress chart
    score_data = []
    for r in tests[-8:]:
        date = str(r["created_at"] or "").split()[0]
        pct = round(r["score"] / r["total"] * 100) if r["total"] else 0
        score_data.append((date, pct))

    chart = _make_ascii_chart(score_data) if score_data else t("no_tests")

    # Topic progress bar
    pending_count = max(0, len(ALL_TOPICS) - learned_count)
    topic_pct = round(learned_count / len(ALL_TOPICS) * 100) if ALL_TOPICS else 0
    topic_bar = _make_progress_bar(topic_pct)
    overall_bar = _make_progress_bar(overall_pct)
    today_bar = _make_progress_bar(today_pct)

    text = (
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *{t('status_title')}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 *Ism:* {name}\n"
        f"{level_emoji} *Daraja:* {level}\n"
        f"📅 *A'zo bo'lgan:* {member_since}\n\n"
        f"━━━━ 📈 PROGRESS ━━━━\n"
        f"🎯 Umumiy ball:  {overall_bar}\n"
        f"📅 Bugungi ball: {today_bar}\n\n"
        f"📚 Mavzular:     {topic_bar}\n"
        f"   ✅ O'rganilgan: {learned_count} | ⏳ Qolgan: {pending_count}\n\n"
        f"📝 Jami testlar:   {total_tests}\n"
        f"💾 Saqlangan so'zlar: {words_count}\n"
        f"⚡ O'quv tezligi:  {tests_per_day} test/kun\n\n"
        f"━━━━ 📊 GRAFIK ━━━━\n"
        f"```\n{chart}\n```\n"
    )

    # Try to send progress chart image
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_status_keyboard(lang)
    )

    # Generate matplotlib chart if possible
    try:
        chart_bytes = await _make_chart_image(score_data, name)
        if chart_bytes:
            bio = io.BytesIO(chart_bytes)
            bio.name = "progress.png"
            await update.message.reply_photo(
                photo=bio,
                caption=f"📈 {t('progress_graph')}"
            )
    except Exception as e:
        logger.error(f"Chart generation failed: {e}")


async def _make_chart_image(score_data: list, name: str) -> bytes | None:
    """Generate a matplotlib bar chart image."""
    if not score_data:
        return None
    try:
        import asyncio
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches

        def _gen():
            dates = [d for d, _ in score_data]
            scores = [s for _, s in score_data]

            fig, ax = plt.subplots(figsize=(10, 5))
            fig.patch.set_facecolor('#0f0f1a')
            ax.set_facecolor('#1a1a2e')

            colors = ['#6366f1' if s >= 70 else '#f59e0b' if s >= 50 else '#ef4444' for s in scores]
            bars = ax.bar(range(len(dates)), scores, color=colors, width=0.6, zorder=3)

            # Value labels on bars
            for bar, score in zip(bars, scores):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
                        f'{score}%', ha='center', va='bottom', color='white',
                        fontweight='bold', fontsize=9)

            ax.set_xticks(range(len(dates)))
            ax.set_xticklabels([d[-5:] for d in dates], color='#a0a0c0', fontsize=8, rotation=20)
            ax.set_yticks([0, 25, 50, 75, 100])
            ax.set_yticklabels(['0%', '25%', '50%', '75%', '100%'], color='#a0a0c0')
            ax.set_ylim(0, 115)

            ax.grid(axis='y', color='#2a2a4a', linestyle='--', linewidth=0.7, zorder=0)
            ax.set_title(f"📊 {name} — Test Natijalari", color='white', fontsize=13, fontweight='bold', pad=12)
            ax.set_xlabel("Sana", color='#a0a0c0', fontsize=9)
            ax.set_ylabel("Ball (%)", color='#a0a0c0', fontsize=9)

            # Legend
            p1 = mpatches.Patch(color='#6366f1', label='≥70% (Yaxshi)')
            p2 = mpatches.Patch(color='#f59e0b', label='50-70% (O\'rta)')
            p3 = mpatches.Patch(color='#ef4444', label='<50% (Kam)')
            ax.legend(handles=[p1, p2, p3], facecolor='#1a1a2e', edgecolor='#6366f1',
                      labelcolor='white', fontsize=8, loc='upper left')

            # Add average line
            if scores:
                avg = sum(scores) / len(scores)
                ax.axhline(y=avg, color='#10b981', linestyle='--', linewidth=1.5,
                           label=f'Avg: {avg:.0f}%', zorder=4)
                ax.text(len(dates) - 0.5, avg + 2, f'Avg: {avg:.0f}%',
                        color='#10b981', fontsize=8, ha='right')

            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#2a2a4a')
            ax.spines['bottom'].set_color('#2a2a4a')
            ax.tick_params(colors='#a0a0c0')

            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=120, bbox_inches='tight',
                        facecolor='#0f0f1a', edgecolor='none')
            plt.close()
            return buf.getvalue()

        return await asyncio.to_thread(_gen)
    except Exception as e:
        logger.error(f"matplotlib chart failed: {e}")
        return None


async def show_learned_topics(message, context, lang: str = "uz", user_id: int = None) -> None:
    """Show list of learned topics with progress graphics."""
    if user_id is None:
        user_id = message.chat_id
    t = lambda k, **kw: get_trans(lang, k, **kw)

    db = await get_db_connection()
    try:
        cursor = await db.execute(
            "SELECT topic_name, topic_key, learned_at FROM user_topics WHERE user_id = ? ORDER BY learned_at DESC",
            (user_id,)
        )
        rows = await cursor.fetchall()
        
        # Also get test scores per topic
        cursor2 = await db.execute(
            "SELECT topic, score, total FROM test_results WHERE user_id = ? ORDER BY created_at DESC LIMIT 50",
            (user_id,)
        )
        all_tests = await cursor2.fetchall()
    finally:
        await db.close()

    if not rows:
        nav_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"📚 {t('pending_topics_title')}", callback_data="status_pending")]
        ])
        await message.reply_text(t("no_learned"), reply_markup=nav_keyboard)
        return

    # Calculate topic scores
    topic_scores = {}
    for test in all_tests:
        tname = test["topic"]
        if tname:
            if tname not in topic_scores:
                topic_scores[tname] = []
            pct = round(test["score"] / test["total"] * 100) if test["total"] else 0
            topic_scores[tname].append(pct)
    
    # Build header with progress bar
    total = len(ALL_TOPICS)
    done = len(rows)
    pct = round(done / total * 100) if total else 0
    bar = _make_progress_bar(pct, 20)
    
    header = (
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ *{t('learned_topics_title')}* ({done}/{total})\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 {bar}\n\n"
    )
    
    # Build topic list with mini progress bars
    lines = []
    for i, r in enumerate(rows):
        date = str(r["learned_at"]).split()[0]
        tname = r["topic_name"]
        tkey = r["topic_key"]
        
        # Find best score for this topic
        best_pct = 0
        for tk, scores in topic_scores.items():
            if tk and (tk.lower() in tname.lower() or tname.lower() in tk.lower() or tkey.lower() in tk.lower()):
                best_pct = max(scores)
        
        if best_pct >= 70:
            icon = "🟢"
        elif best_pct >= 50:
            icon = "🟡"
        elif best_pct > 0:
            icon = "🟠"
        else:
            icon = "✅"
        
        mini_bar = ""
        if best_pct > 0:
            filled = round(best_pct / 100 * 8)
            mini_bar = f" [{'█' * filled}{'░' * (8 - filled)}] {best_pct}%"
        
        lines.append(f"{icon} *{tname}*{mini_bar}")
        lines.append(f"   📅 {date}")
    
    nav_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📚 {t('pending_topics_title')}", callback_data="status_pending")]
    ])
    
    # Split into chunks of 8 topics per message
    chunk_size = 8
    chunks = [lines[i:i+chunk_size*2] for i in range(0, len(lines), chunk_size*2)]
    
    for chunk in chunks:
        await message.reply_text(
            header + "\n".join(chunk),
            parse_mode="Markdown",
            reply_markup=nav_keyboard
        )


async def show_pending_topics(message, context, lang: str = "uz", user_id: int = None) -> None:
    """Show topics not yet learned with visual indicators."""
    if user_id is None:
        user_id = message.chat_id
    t = lambda k, **kw: get_trans(lang, k, **kw)

    db = await get_db_connection()
    try:
        cursor = await db.execute(
            "SELECT topic_key FROM user_topics WHERE user_id = ?", (user_id,)
        )
        learned_keys = {r["topic_key"] for r in await cursor.fetchall()}
    finally:
        await db.close()

    pending = [topic for topic in ALL_TOPICS if not _topic_is_learned(topic, learned_keys)]

    if not pending:
        nav_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"✅ {t('learned_topics_title')}", callback_data="status_learned")]
        ])
        await message.reply_text(
            "🏆 Barcha mavzularni o'rgandingiz! Ajoyib!",
            reply_markup=nav_keyboard
        )
        return

    total = len(ALL_TOPICS)
    done = total - len(pending)
    pct = round(done / total * 100) if total else 0
    bar = _make_progress_bar(pct, 20)
    
    header = (
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📚 *{t('pending_topics_title')}* ({len(pending)}/{total})\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 {bar}\n\n"
    )
    
    lines = []
    for i, topic in enumerate(pending):
        # Difficulty indicator based on topic position
        if i < 5:
            diff = "🌱"  # Easy
        elif i < 12:
            diff = "🌿"  # Medium
        else:
            diff = "🌳"  # Advanced
        lines.append(f"{diff} ⏳ *{topic}*")
    
    nav_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"✅ {t('learned_topics_title')}", callback_data="status_learned")]
    ])
    
    # Split into chunks
    chunk_size = 10
    chunks = [lines[i:i+chunk_size] for i in range(0, len(lines), chunk_size)]
    
    for chunk in chunks:
        await message.reply_text(
            header + "\n".join(chunk),
            parse_mode="Markdown",
            reply_markup=nav_keyboard
        )
