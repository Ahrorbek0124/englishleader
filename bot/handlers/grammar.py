from telegram import Update
from telegram.ext import ContextTypes
from bot.utils.keyboards import get_grammar_topics_menu, get_grammar_action_buttons
from bot.database.db import get_user_lang

GRAMMAR_DATA = {
    "Articles": """📌 Articles — Artikllar (a / an / the)

📖 Izoh: Ingliz tilida 3 ta artikl bor.
• A / An — noaniq (birinchi marta tilga olinayotgan)
• The — aniq (ma'lum bo'lgan predmet)
• Zero article — artikl qo'yilmaydi (ism, shahar, sport, til)

📐 Qoidalar:
1. A — undosh tovush bilan boshlangan so'z oldidan: a book, a car
2. An — unli tovush bilan boshlangan so'z oldidan: an apple, an hour
3. The — aniq predmet, yagona narsalar: the sun, the moon
4. Artikl yo'q: breakfast, lunch, school, home, by car

✅ Misollar:
• I saw a dog. The dog was big.
• She is a doctor.
• The Nile is the longest river.
• I go to school by bus.

⚠️ Xatolar:
❌ I am the student → ✅ I am a student
❌ She plays the tennis → ✅ She plays tennis""",

    "Prepositions": """📌 Prepositions — Predloglar (in / on / at)

📐 Vaqt predloglari:
• IN — yil, oy, fasl: in 2024, in May, in winter
• ON — kun, sana: on Monday, on March 5
• AT — aniq vaqt: at 3 PM, at Christmas
• FOR — davomiylik: for 2 hours
• SINCE — boshlanish: since 2010
• BY — muddatgacha: by Friday

📐 Joy predloglari:
• IN — ichida: in the box, in London
• ON — ustida: on the table, on the bus
• AT — aniq nuqta: at the door, at school

✅ Misollar:
• I was born in 1995.
• The meeting is on Monday at 9 AM.
• She has lived here since 2015.

⚠️ Xatolar:
❌ I was born on 1995 → ✅ in 1995
❌ I will call you in Monday → ✅ on Monday""",

    "Modal Verbs": """📌 Modal Verbs — Modal Fe'llar

📐 Asosiy modal fe'llar:
• CAN — qobiliyat: I can swim.
• COULD — o'tgan qobiliyat: She could read at 4.
• MUST — kuchli majburiyat: You must stop.
• HAVE TO — tashqi majburiyat: I have to work.
• SHOULD — maslahat: You should eat fruit.
• MAY — rasmiy ruxsat: May I come in?
• MIGHT — kamroq ehtimol: He might be late.
• WILL — kelajak: I will call you.
• WOULD — shart: I would go if I could.

✅ Misollar:
• You must be tired.
• Could you pass the salt?
• She might not come.
• You don't have to pay.

⚠️ Xatolar:
❌ You must to go → ✅ You must go""",

    "Conditionals": """📌 Conditionals — Shart Gaplari

🔹 ZERO — Umumiy haqiqatlar:
If + Pr.Simple, Pr.Simple
• If you heat water to 100°C, it boils.

🔹 FIRST — Haqiqiy kelajak shart:
If + Pr.Simple, will + V1
• If I study hard, I will pass.

🔹 SECOND — Xayoliy shart:
If + Past Simple, would + V1
• If I were rich, I would travel.

🔹 THIRD — O'tgan xayoliy:
If + Past Perfect, would have + V3
• If I had studied, I would have passed.

⚠️ Xatolar:
❌ If I will see him → ✅ If I see him
❌ If I would be rich → ✅ If I were rich""",

    "Passive Voice": """📌 Passive Voice — Majhul Nisbat

Shakl: Object + be + V3

Present Simple:   am/is/are + V3
Past Simple:      was/were + V3
Present Perfect:  have/has been + V3
Future Simple:    will be + V3
Modal + Passive:  modal + be + V3

✅ Misollar:
• Cars are made here. (Active: They make cars)
• My wallet was stolen.
• The flight has been cancelled.
• The winner will be announced.
• The book was written by Tolstoy.

⚠️ Xatolar:
❌ The letter is wrote → ✅ is written
❌ It was builded → ✅ It was built""",

    "Reported Speech": """📌 Reported Speech — Bilvosita Nutq

📐 Zamon o'zgarishi:
Present Simple  → Past Simple
Present Cont.   → Past Continuous
Present Perfect → Past Perfect
Past Simple     → Past Perfect
Will            → Would / Can → Could

📐 So'roq gaplar:
"Where do you live?" → He asked where I lived.
"Are you tired?" → She asked if I was tired.

📐 Buyruq gaplar:
"Close the door!" → He told me to close the door.

📐 O'zgaradigan so'zlar:
now→then, today→that day, here→there
tomorrow→the next day, this→that

⚠️ Xatolar:
❌ She said me that → ✅ She told me that""",

    "Gerunds & Infinitives": """📌 Gerunds & Infinitives

📐 Gerund (V+ing) ishlatish:
After: enjoy, avoid, finish, mind, suggest, keep
• I enjoy swimming.
After prepositions:
• He is good at cooking.

📐 Infinitive (to+V1) ishlatish:
After: want, need, hope, plan, decide, agree
• I want to go.
After adjectives:
• It's easy to understand.

📐 Farqli ma'no:
• remember +ing = o'tgan: I remember locking the door.
• remember +to = kelajak: Remember to lock the door.
• stop +ing = to'xtatish: He stopped smoking.
• stop +to = uchun: He stopped to smoke.

⚠️ Xatolar:
❌ I enjoy to read → ✅ I enjoy reading
❌ She agreed going → ✅ She agreed to go""",

    "Comparatives": """📌 Comparatives & Superlatives

📐 Qisqa sifatlar (1-2 bo'g'in):
Comparative: sifat + -er + than
• tall → taller, fast → faster
Superlative: the + sifat + -est
• tall → the tallest

📐 Uzun sifatlar (3+ bo'g'in):
Comparative: more + sifat + than
Superlative: the most + sifat

📐 Noto'g'ri shakllar:
good→better→the best
bad→worse→the worst
far→farther→the farthest

📐 Tenglash:
• as...as: She is as tall as her sister.
• The harder you work, the better results.

⚠️ Xatolar:
❌ more taller → ✅ taller
❌ the most tallest → ✅ the tallest""",

    "Phrasal Verbs": """📌 Phrasal Verbs — Top 30

• ask out — romantik taklif
• back up — qo'llab-quvvatlash
• break down — buzilmoq
• break up — ajrashmoq
• bring up — tarbiyalash
• call off — bekor qilish
• carry on — davom ettirish
• come across — tasodifan uchratish
• come up with — g'oya topish
• give up — voz kechish
• go over — ko'rib chiqish
• hang out — birga vaqt o'tkazish
• look after — g'amxo'rlik qilish
• look forward to — kutish
• look into — tekshirish
• make up — yarashtirish
• pick up — ko'tarish/o'rganish
• put off — kechiktirish
• put up with — chidash
• run into — tasodifan uchrashish
• run out of — tugash
• set up — tashkil qilish
• show up — paydo bo'lish
• take off — uchish/yechish
• take on — qabul qilish
• take up — boshlamoq (hobby)
• turn down — rad etish
• turn out — ma'lum bo'lish
• work out — sport/hal qilish""",

    "Idioms": """📌 Idioms — Ko'chma Ma'noli Iboralar

🔹 Oson narsalar:
• Piece of cake — Juda oson
• No-brainer — Aniq javob

🔹 Vaqt:
• Once in a blue moon — Juda kam
• In the nick of time — Zo'rg'a vaqtida
• Hit the sack — Uxlamoq
• Burn the midnight oil — Kech gacha ishlash

🔹 Muloqot:
• Beat around the bush — Atrofida aylanish
• Spill the beans — Sirni oshkor qilish
• Hit the nail on the head — To'g'ri aytish

🔹 Holat:
• Under the weather — Kasal
• On cloud nine — Juda xursand
• Break a leg — Omad tilamoq
• In hot water — Muammoda

🔹 Bilim:
• Know the ropes — Tajribali
• Learn the ropes — O'rganmoq
• Scratch the surface — Yuza ko'rish""",

    "Tenses Overview": """📌 16 Ingliz Tili Zamoni — Umumiy Ko'rinish

⏰ PRESENT:
1. Present Simple: I work
2. Present Continuous: I am working
3. Present Perfect: I have worked
4. Present Perfect Cont.: I have been working

🕰️ PAST:
5. Past Simple: I worked
6. Past Continuous: I was working
7. Past Perfect: I had worked
8. Past Perfect Cont.: I had been working

🔮 FUTURE:
9. Future Simple: I will work
10. Be Going To: I am going to work
11. Future Continuous: I will be working
12. Future Perfect: I will have worked""",

    "Word Order": """📌 Word Order — Gap Tartibi

📐 Asosiy tartib: S + V + O + Place + Time
• She reads books at home every evening.

📐 Frequency ravishlar:
to be → keyin: She is always happy.
Oddiy fe'l → oldin: I always wake up early.

📐 Inversion:
Never/Rarely gap boshida:
Never have I seen such beauty.

✅ Misollar:
• I usually go to work by bus. ✅
• She has never been to Japan. ✅

⚠️ Xatolar:
❌ I go usually to work → ✅ I usually go""",
}


async def show_grammar_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    lang    = await get_user_lang(user_id)
    context.user_data['state'] = "grammar"
    topics  = list(GRAMMAR_DATA.keys())
    await update.message.reply_text(
        "📚 *Grammar mavzusini tanlang:*",
        parse_mode="Markdown",
        reply_markup=get_grammar_topics_menu(topics, lang)
    )


async def handle_grammar_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text    = update.message.text
    user_id = update.effective_user.id
    lang    = await get_user_lang(user_id)
    if text in GRAMMAR_DATA:
        topic_key = text.replace(" ", "_")
        await update.message.reply_text(
            GRAMMAR_DATA[text],
            reply_markup=get_grammar_action_buttons(topic_key, lang)
        )
