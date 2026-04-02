from telegram import Update
from telegram.ext import ContextTypes
from bot.utils.keyboards import get_tenses_menu, get_tenses_nav_buttons
from bot.database.db import get_user_lang

TENSES_DATA = {
    1: """📌 Present Simple — Hozirgi Oddiy Zamon

📐 Shakl:
(+) Subject + V1 / V1+s/es (u/she/it uchun)
(-) Subject + don't / doesn't + V1
(?) Do / Does + Subject + V1?

📖 Qachon ishlatiladi:
1. Doimiy odatlar va takrorlanuvchi ishlar
2. Umumiy haqiqatlar va ilmiy faktlar
3. Jadval/timetable bo'yicha kelajak
4. Ko'rsatmalar va retseptlar

✅ Misollar:
• I work at a hospital. — Men kasalxonada ishlayman.
• She drinks coffee every morning. — U har ertalab qahva ichadi.
• Water boils at 100°C. — Suv 100°C da qaynaydi.
• The train leaves at 7 AM. — Poyezd 7:00 da ketadi.
• Does he speak English? — U ingliz tilida gapiradimi?
• I don't like spicy food. — Men achchiq ovqatni yoqtirmayman.

⏱ Vaqt belgilari:
always, usually, often, sometimes, rarely, never,
every day/week/year, on Mondays, at weekends,
in the morning, once a week

📝 Imlo qoidalari (he/she/it):
• -s: work→works, play→plays
• -es: watch→watches, go→goes, do→does
• -ies: study→studies, carry→carries

⚠️ Xatolar:
❌ She work every day → ✅ She works every day
❌ Do he like pizza? → ✅ Does he like pizza?
❌ I am go to school → ✅ I go to school

🎬 https://www.youtube.com/results?search_query=present+simple+uzbek+ingliz+tili""",

    2: """📌 Present Continuous — Hozirgi Davomli Zamon

📐 Shakl:
(+) Subject + am/is/are + V-ing
(-) Subject + am/is/are + not + V-ing
(?) Am/Is/Are + Subject + V-ing?

📖 Qachon ishlatiladi:
1. Hozir, shu daqiqada bo'layotgan ishlar
2. Vaqtinchalik holatlar (doimiy emas)
3. Oldindan rejalashtirilgan yaqin kelajak
4. O'zgarayotgan holatlar (tendensiya)

✅ Misollar:
• I am studying right now. — Men hozir o'qiyapman.
• She is talking on the phone. — U telefonda gapiryapti.
• They are staying at a hotel this week. — Bu hafta ular mehmonxonada turishyapti.
• I'm meeting Tom tomorrow. — Ertaga Tom bilan uchrashaman.
• Prices are rising. — Narxlar ko'tarilmoqda.

⏱ Vaqt belgilari:
now, right now, at the moment, currently, 
at present, today, this week, look! listen!
tomorrow (reja uchun), tonight

🚫 Davomli bo'lmaydigan fe'llar (State verbs):
love, like, hate, want, need, know, believe,
understand, remember, see, hear, smell, taste,
belong, contain, seem, appear, have (ega bo'lish)
→ Bu fe'llar odatda Present Continuous bilan ISHLATILMAYDI
❌ I am knowing the answer → ✅ I know the answer

📝 -ing qo'shish qoidalari:
• Oddiy: work→working, play→playing
• -e bilan tugasa: come→coming, make→making
• CVC (qisqa): run→running, sit→sitting

⚠️ Xatolar:
❌ She is work → ✅ She is working
❌ I am wanting tea → ✅ I want tea
❌ Are you know him? → ✅ Do you know him?

🎬 https://www.youtube.com/results?search_query=present+continuous+uzbek""",

    3: """📌 Present Perfect — Hozirgi Tugallangan Zamon

📐 Shakl:
(+) Subject + have/has + V3 (past participle)
(-) Subject + haven't/hasn't + V3
(?) Have/Has + Subject + V3?

📖 Qachon ishlatiladi:
1. Natijasi hozir ko'rinadigan o'tgan ish
2. Hayotiy tajriba (ever/never)
3. Yaqinda bo'lgan ish (just/recently)
4. Hozirga qadar davom etayotgan holat (for/since)
5. Birinchi/uchinchi marta

✅ Misollar:
• I have lost my keys. — Kalitlarimni yo'qotib qo'ydim. (hozir yo'q)
• She has visited Paris twice. — U Parijga ikki marta borgan.
• Have you ever eaten sushi? — Siz hech sushi yegan bo'lganmisiz?
• I have just finished my homework. — Men hozirgina uy ishimni tugatdim.
• He hasn't called yet. — U hali qo'ng'iroq qilmadi.
• They have lived here for 5 years. — Ular bu yerda 5 yildan beri yashashmoqda.
• This is the best film I have ever seen. — Bu men ko'rgan eng yaxshi film.

⏱ Vaqt belgilari:
just, already, yet (so'roq/inkor), ever, never,
recently, lately, so far, up to now,
for (davomiylik: for 3 years), since (boshlanish: since 2020),
this week/month/year, today

📊 Past Simple vs Present Perfect:
Past Simple: aniq vaqt belgilangan → Yesterday I saw him.
Present Perfect: vaqt noaniq/hozirga bog'liq → I have seen him.

❌ I saw him yesterday ✅ (aniq vaqt: yesterday)
❌ Have you seen him yesterday? → ✅ Did you see him yesterday?

⚠️ Xatolar:
❌ I have went → ✅ I have gone
❌ She has saw → ✅ She has seen
❌ Did you ever eat sushi? → ✅ Have you ever eaten sushi?

🎬 https://www.youtube.com/results?search_query=present+perfect+uzbek+tense""",

    4: """📌 Present Perfect Continuous — Hozirgi Tugallangan Davomli Zamon

📐 Shakl:
(+) Subject + have/has been + V-ing
(-) Subject + haven't/hasn't been + V-ing
(?) Have/Has + Subject + been + V-ing?

📖 Qachon ishlatiladi:
1. O'tmishda boshlangan va hali davom etayotgan ish
2. Yaqinda tugagan, ammo natijasi ko'rinayotgan ish
3. Qancha vaqtdan beri ekanligini ko'rsatish (how long)

✅ Misollar:
• I have been studying for 3 hours. — Men 3 soatdan beri o'qiyapman.
• She has been working here since 2019. — U 2019 yildan beri bu yerda ishlamoqda.
• How long have you been waiting? — Qancha vaqtdan beri kutayapsiz?
• They have been building that house for months. — Ular oy-oylardan beri o'sha uyni qurmoqda.
• You look tired. Have you been running? — Charchagan ko'rinasiz. Yugurdingizmi?

⏱ Vaqt belgilari:
for, since, how long, all day/morning/week,
lately, recently (process uchun)

📊 Present Perfect vs Pres. Perfect Continuous:
Perfect: natija muhim → I have written 3 emails.
Perfect Cont.: jarayon muhim → I have been writing emails all morning.

Perfect: tugagan ish → She has read the book.
Perfect Cont.: hali davom etmoqda → She has been reading the book.

⚠️ Xatolar:
❌ I have been know him → ✅ I have known him (state verb)
❌ She has been worked → ✅ She has been working

🎬 https://www.youtube.com/results?search_query=present+perfect+continuous+uzbek""",

    5: """📌 Past Simple — O'tgan Oddiy Zamon

📐 Shakl:
(+) Subject + V2 (past form)
(-) Subject + didn't + V1
(?) Did + Subject + V1?

📖 Qachon ishlatiladi:
1. O'tmishda aniq vaqtda tugallangan ishlar
2. Ketma-ket hodisalar (hikoya)
3. O'tmishdagi odatlar (used to bilan ham)
4. Aniq vaqt belgilangan barcha o'tgan ishlar

✅ Misollar:
• I visited London last year. — Men o'tgan yil Londonga bordim.
• She didn't come to the party. — U ziyofatga kelmadi.
• Did you watch the match? — Matchni ko'rdingizmi?
• He woke up, had breakfast and left. — U uyg'ondi, nonushta qildi va ketdi.
• We used to play football every day. — Biz har kuni futbol o'ynardik.

⏱ Vaqt belgilari:
yesterday, last week/month/year, ago (2 days ago),
in 1999 / in the 1990s, on Monday, at 3 PM,
when I was young, once, then, after that, finally

📝 Noto'g'ri fe'llar (Irregular verbs — asosiylar):
go → went, come → came, see → saw,
take → took, give → gave, get → got,
have → had, do → did, make → made,
know → knew, think → thought, say → said,
tell → told, find → found, leave → left,
begin → began, write → wrote, read → read,
buy → bought, bring → brought, eat → ate,
drink → drank, speak → spoke, run → ran

⚠️ Xatolar:
❌ I goed → ✅ I went
❌ She didn't went → ✅ She didn't go
❌ Did he went? → ✅ Did he go?

🎬 https://www.youtube.com/results?search_query=past+simple+uzbek+ingliz+tili""",

    6: """📌 Past Continuous — O'tgan Davomli Zamon

📐 Shakl:
(+) Subject + was/were + V-ing
(-) Subject + wasn't/weren't + V-ing
(?) Was/Were + Subject + V-ing?

📖 Qachon ishlatiladi:
1. O'tmishda aniq bir vaqtda davom etayotgan ish
2. Uzilgan harakat (when/while bilan)
3. O'tmishda parallel davom etgan ikki ish
4. Fon tasvirida (hikoya background)

✅ Misollar:
• I was watching TV at 8 PM. — Kecha soat 8 da TV ko'rayotgan edim.
• She was sleeping when I called. — Men qo'ng'iroq qilganimda u uxlayotgan edi.
• While I was cooking, he was setting the table. — Men ovqat pishirayotganda u dasturxon yozayotgan edi.
• It was raining when we arrived. — Biz kelganimizda yomg'ir yog'ayotgan edi.
• They weren't listening to the teacher. — Ular o'qituvchini tinglayotgan emasdilar.

⏱ Vaqt belgilari:
while (davomli ish uchun), when (uzilish uchun),
at that moment, at 8 PM yesterday, all morning,
as (ikki parallel ish), just as

📊 Past Simple vs Past Continuous:
Past Simple: tugallangan qisqa ish
Past Continuous: o'sha paytda davom etayotgan ish

While I was walking (Cont.), I saw (Simple) an accident.
When the phone rang (Simple), I was sleeping (Cont.).

⚠️ Xatolar:
❌ I was go → ✅ I was going
❌ She were working → ✅ She was working
❌ Were they knowing? → ✅ Did they know? (state verb)

🎬 https://www.youtube.com/results?search_query=past+continuous+uzbek""",

    7: """📌 Past Perfect — O'tgan Tugallangan Zamon

📐 Shakl:
(+) Subject + had + V3
(-) Subject + hadn't + V3
(?) Had + Subject + V3?

📖 Qachon ishlatiladi:
1. O'tmishdagi boshqa bir ishdan OLDIN tugallangan ish
2. Sabab-natija ketma-ketligi
3. Reported speech (zamon siljishi)
4. Third conditional shart gaplarida

✅ Misollar:
• When I arrived, she had already left. — Men kelganimda u allaqachon ketib bo'lgan edi.
• He had never seen snow before he moved to Canada. — U Kanadaga ko'chishdan oldin hech qor ko'rmagan edi.
• I was tired because I had worked all night. — Men charchagan edim, chunki butun kecha ishlaganman.
• Had you met him before the party? — Ziyofatdan oldin u bilan tanishgan edingizmi?
• She said that she had finished the report. — U hisobotni tugatganligi haqida aytdi.

⏱ Vaqt belgilari:
before, after, already, just, never (before),
by the time, when, as soon as, because,
by + time: By 5 PM, she had finished.

📊 Past Simple vs Past Perfect:
Agar ikkita o'tgan zamon bo'lsa:
OLDINROQ bo'lgan ish → Past Perfect
KEYINROQ bo'lgan ish → Past Simple

She left (PS) before I arrived (PS). ← ketma-ket
She had left (PP) when I arrived (PS). ← u oldin ketdi

⚠️ Xatolar:
❌ I had went → ✅ I had gone
❌ After she left, I had arrived → ✅ After she had left, I arrived
❌ Had she went? → ✅ Had she gone?

🎬 https://www.youtube.com/results?search_query=past+perfect+uzbek""",

    8: """📌 Past Perfect Continuous — O'tgan Tugallangan Davomli Zamon

📐 Shakl:
(+) Subject + had been + V-ing
(-) Subject + hadn't been + V-ing
(?) Had + Subject + been + V-ing?

📖 Qachon ishlatiladi:
1. O'tmishdagi ma'lum bir nuqtadan oldin davom etgan jarayon
2. Sababni ko'rsatish (charchoq, natija sababi)
3. Qancha vaqt davom etganini ko'rsatish (o'tmishda)

✅ Misollar:
• She was tired because she had been working all day.
  — U charchagan edi, chunki kun bo'yi ishlagan edi.
• I had been waiting for 2 hours when he finally arrived.
  — U nihoyat kelganda men 2 soatdan beri kutgan edim.
• How long had you been studying before the exam?
  — Imtihondan oldin qancha vaqt o'qigansiz?
• It had been raining for hours before it stopped.
  — To'xtashidan oldin soatlab yomg'ir yog'ib turgan edi.

⏱ Vaqt belgilari:
for, since, how long, before, when, all day/morning,
by the time (+ Past Simple)

📊 Taqqoslash:
Past Perfect: natija muhim → I had written 10 pages.
Past Perf. Cont.: jarayon muhim → I had been writing all night.

⚠️ Xatolar:
❌ I had been know → ✅ I had known (state verb)
❌ She had been worked → ✅ She had been working

🎬 https://www.youtube.com/results?search_query=past+perfect+continuous+uzbek""",

    9: """📌 Future Simple (will) — Kelajak Oddiy Zamon

📐 Shakl:
(+) Subject + will + V1
(-) Subject + won't (will not) + V1
(?) Will + Subject + V1?

📖 Qachon ishlatiladi:
1. Hozir qabul qilingan spontan qaror
2. Bashorat va taxmin (ehtimol)
3. Va'da, taklif, tahdid
4. So'rov va iltimos (Will you...?)
5. Shartli gaplarda natija qismi (First Conditional)

✅ Misollar:
• I'll have the soup, please. — Menga sho'rva bering. (hozir qaror qildi)
• It will rain tomorrow. — Ertaga yomg'ir yog'adi.
• I won't tell anyone your secret. — Sirингizni hech kimga aytmayman. (va'da)
• Will you help me? — Menga yordam berasizmi?
• She'll probably call later. — U keyinroq, ehtimol, qo'ng'iroq qiladi.
• If you work hard, you will succeed. — Qattiq ishlasangiz, muvaffaq bo'lasiz.

⏱ Vaqt belgilari:
tomorrow, next week/month/year, soon, later,
in the future, in 2030, probably, perhaps, maybe,
I think, I'm sure, I believe, I expect

📊 Will vs Be Going To:
Will: spontan qaror, bashorat (dalilsiz)
Going To: oldindan rejalashtirilgan, dalilga asoslangan bashorat

(Telefon jiringlaydi) I'll answer it! ← spontan
I'm going to call him tonight. ← oldindan reja

⚠️ Xatolar:
❌ I will to go → ✅ I will go
❌ She will goes → ✅ She will go
❌ Will you can help? → ✅ Will you be able to help?

🎬 https://www.youtube.com/results?search_query=future+simple+will+uzbek""",

    10: """📌 Be Going To — Rejalashtirilgan Kelajak

📐 Shakl:
(+) Subject + am/is/are + going to + V1
(-) Subject + am/is/are + not + going to + V1
(?) Am/Is/Are + Subject + going to + V1?

📖 Qachon ishlatiladi:
1. Oldindan rejalashtirilgan niyat va rejalar
2. Dalilga asoslangan bashorat (hozir ko'rinadigan belgilar)
3. Yaqin kelajakda sodir bo'lishi aniq ishlar

✅ Misollar:
• I'm going to visit my parents this weekend.
  — Bu dam olish kunida ota-onamni ziyorat qilmoqchiman. (reja)
• Look at those clouds! It's going to rain.
  — O'sha bulutlarga qarang! Yomg'ir yog'adi. (dalil bor)
• She is going to have a baby. — U homilador.
• Are you going to apply for that job? — O'sha ishga ariza berasizmi?
• We're not going to make it in time. — Biz vaqtida yeta olmaymiz.

⏱ Vaqt belgilari:
tonight, tomorrow, next week/month,
this weekend, soon, in the near future,
this summer, next year

📊 Going To vs Present Continuous (future):
Ikkalasi ham rejalashtirilgan kelajak uchun.
Present Continuous: aniq tashkil qilingan ijtimoiy reja
Going To: niyat, maqsad

I'm meeting John at 3. (uchrashув aniq) ← Pres. Cont.
I'm going to meet John soon. (niyat) ← Going To

⚠️ Xatolar:
❌ I am going to went → ✅ I am going to go
❌ She is going to works → ✅ She is going to work
❌ Are you going to the cinema? (mavjud, biroq ma'no boshqa: bu reja emas, joy)

🎬 https://www.youtube.com/results?search_query=be+going+to+uzbek""",

    11: """📌 Future Continuous — Kelajak Davomli Zamon

📐 Shakl:
(+) Subject + will be + V-ing
(-) Subject + won't be + V-ing
(?) Will + Subject + be + V-ing?

📖 Qachon ishlatiladi:
1. Kelajakdagi aniq bir vaqtda davom etayotgan ish
2. Kutilayotgan yoki rejalashtirilgan davomli ish
3. Nazokat bilan so'rash (birovning rejalari haqida)
4. Parallel kelajak ishlar

✅ Misollar:
• At 8 PM tomorrow, I will be watching the match.
  — Ertaga soat 8 da men matchni ko'rayotgan bo'laman.
• This time next week, we'll be flying to Paris.
  — Keyingi hafta shu payt biz Parijga uchib borayotgan bo'lamiz.
• Will you be using the car tonight? (nazokat bilan so'rash)
  — Bugun kechqurun mashinadan foydalanasizmi?
• While you're sleeping, I'll be working.
  — Siz uxlayotganingizda men ishlaB turaman.

⏱ Vaqt belgilari:
at this time tomorrow, this time next week,
at 8 PM tomorrow, all day tomorrow,
while, when (+ future), in 2 hours from now

📊 Future Simple vs Future Continuous:
Future Simple: bir lahzali kelajak ish → I will call you.
Future Continuous: davomli kelajak ish → I will be calling you all evening.

⚠️ Xatolar:
❌ I will be go → ✅ I will be going
❌ She will being working → ✅ She will be working

🎬 https://www.youtube.com/results?search_query=future+continuous+uzbek""",

    12: """📌 Future Perfect — Kelajak Tugallangan Zamon

📐 Shakl:
(+) Subject + will have + V3
(-) Subject + won't have + V3
(?) Will + Subject + have + V3?

📖 Qachon ishlatiladi:
1. Kelajakdagi aniq bir muddatgacha tugallanishi kutilayotgan ish
2. Kelajakda bir ish boshqa ishdan OLDIN tugallanishi
3. Hisob-kitob va taxminlar (ma'lum vaqtga kelib)

✅ Misollar:
• By Friday, I will have finished the project.
  — Juma kuniga qadar loyihani tugatgan bo'laman.
• By the time you arrive, we will have eaten.
  — Siz kelguncha biz ovqatlanib bo'lgan bo'lamiz.
• She will have graduated by next summer.
  — Keyingi yozgacha u tugatgan bo'ladi.
• Will you have finished by 5 PM?
  — Soat 5 ga qadar tugatasizmi?
• By 2030, scientists will have found a cure.
  — 2030 yilga kelib, olimlar davo topgan bo'ladi.

⏱ Vaqt belgilari:
by + time (by tomorrow, by 5 PM, by next year, by 2030),
by the time + clause,
before + time,
in 10 years' time

📊 Future Perfect vs Future Simple:
Future Simple: kelajakda bo'ladigan ish → I will finish it.
Future Perfect: ma'lum muddatgacha tugallanishi → I will have finished it by Friday.

📌 Future Perfect Continuous (bonus):
Shakl: will have been + V-ing
Maqsad: muddatgacha davom etgan jarayonni ko'rsatish
• By noon, I will have been working for 6 hours.
  — Tushga qadar 6 soatdan beri ishlayotgan bo'laman.

⚠️ Xatolar:
❌ I will have went → ✅ I will have gone
❌ She will have finished until Friday → ✅ by Friday
❌ Will you have finish? → ✅ Will you have finished?

🎬 https://www.youtube.com/results?search_query=future+perfect+uzbek""",
}

# Keyboard tugmalari → Tense ID xaritasi (keyboards.py dagi nomlarga mos)
TENSE_MAPPING = {
    "⏰ Present Simple":      1,
    "🔄 Present Continuous":  2,
    "✅ Present Perfect":     3,
    "🔁 Pres. Perfect Cont.": 4,
    "🕰️ Past Simple":         5,
    "🔄 Past Continuous":     6,
    "✔️ Past Perfect":        7,
    "🔁 Past Perfect Cont.":  8,
    "🔮 Future Simple":       9,
    "📅 Be Going To":         10,
    "🔄 Future Continuous":   11,
    "✅ Future Perfect":      12,
}


async def show_tenses_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['state'] = "tenses"
    await update.message.reply_text(
        "📚 12 ta Ingliz tili zamoni — o'rganish uchun birini tanlang:",
        reply_markup=get_tenses_menu()
    )


async def handle_tense_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    if text in TENSE_MAPPING:
        t_id = TENSE_MAPPING[text]
        await send_tense_lesson(update.message, t_id)


async def send_tense_lesson(message, tense_id: int):
    if tense_id in TENSES_DATA:
        await message.reply_text(
            TENSES_DATA[tense_id],
            reply_markup=get_tenses_nav_buttons(tense_id),
            disable_web_page_preview=True
        )
    else:
        await message.reply_text("❌ Bu zamon ma'lumoti topilmadi.")


async def show_tense_info(update: Update, context: ContextTypes.DEFAULT_TYPE, tense_id: int):
    """Callback orqali chaqiriladi."""
    query = update.callback_query
    if tense_id in TENSES_DATA:
        await query.message.reply_text(
            TENSES_DATA[tense_id],
            reply_markup=get_tenses_nav_buttons(tense_id),
            disable_web_page_preview=True
        )
    else:
        await query.message.reply_text("❌ Bu zamon topilmadi.")


async def handle_tense_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("tense_"):
        try:
            t_id = int(data.split("_")[1])
            await send_tense_lesson(query.message, t_id)
        except (ValueError, IndexError):
            await query.message.reply_text("❌ Noto'g'ri zamon ID.")

    elif data.startswith("quiz_tense_"):
        try:
            t_id = int(data.replace("quiz_tense_", ""))
            topic = TENSES_DATA[t_id].split("\n")[0].replace("📌", "").strip()
            from bot.handlers.tests import start_quiz
            await start_quiz(query.message, context, topic=topic, count=5)
        except Exception as e:
            await query.message.reply_text(f"❌ Quiz yaratishda xatolik: {e}")
