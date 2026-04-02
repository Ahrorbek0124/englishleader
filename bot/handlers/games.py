import random
from telegram import Update
from telegram.ext import ContextTypes
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from bot.database.db import get_db_connection, get_user_lang, get_game_progress, save_game_progress
from bot.services.i18n import get_trans

# ─── Game Data: 8 levels (A1-SAT), 3 topics each, 3 game modes ───────────────
GAME_LEVELS = {
    "A1": {
        "title_en": "Beginner", "title_uz": "Boshlang'ich",
        "xp_required": 0,
        "topics": {
            "greetings": {
                "title_en": "Greetings & Introductions", "title_uz": "Salomlashish",
                "emoji": "👋",
                "quiz": [
                    {"q": "How do you say 'Hello' formally?", "options": ["Hey", "Good morning", "Yo", "Hiya"], "answer": 1},
                    {"q": "What does 'Nice to meet you' mean in Uzbek?", "options": ["Xayrli kun", "Tanishganimdan xursandman", "Qalaysiz", "Rahmat"], "answer": 1},
                    {"q": "Correct response to 'How are you'?", "options": ["I am have good", "I am fine, thank you", "I good am", "Yes I am"], "answer": 1},
                    {"q": "What is 'Goodbye' casually?", "options": ["See you later", "Good evening", "Welcome", "Please"], "answer": 0},
                    {"q": "How to introduce yourself?", "options": ["My name it is...", "I name is...", "My name is...", "Name my is..."], "answer": 2},
                ],
                "word_match": [
                    ("Hello", "Salom"), ("Goodbye", "Xayr"), ("Thank you", "Rahmat"),
                    ("Please", "Iltimos"), ("Good morning", "Xayrli tong"),
                ],
                "sentence_build": [
                    {"words": ["name", "My", "is", "John", "."], "answer": "My name is John."},
                    {"words": ["to", "Nice", "meet", "you", "!"], "answer": "Nice to meet you!"},
                    {"words": ["How", "are", "you", "?"], "answer": "How are you?"},
                ],
            },
            "numbers_colors": {
                "title_en": "Numbers & Colors", "title_uz": "Sonlar va ranglar",
                "emoji": "🔢",
                "quiz": [
                    {"q": "What number is 'seven'?", "options": ["5", "6", "7", "8"], "answer": 2},
                    {"q": "Sky color on clear day?", "options": ["Green", "Blue", "Red", "Yellow"], "answer": 1},
                    {"q": "'oq' (white) in English?", "options": ["Black", "Brown", "White", "Grey"], "answer": 2},
                    {"q": "What is 'fifteen'?", "options": ["13", "14", "15", "50"], "answer": 2},
                    {"q": "What color is a banana?", "options": ["Red", "Blue", "Green", "Yellow"], "answer": 3},
                ],
                "word_match": [("One", "Bir"), ("Two", "Ikki"), ("Red", "Qizil"), ("Blue", "Ko'k"), ("Green", "Yashil")],
                "sentence_build": [
                    {"words": ["is", "The", "apple", "red", "."], "answer": "The apple is red."},
                    {"words": ["I", "have", "three", "books", "."], "answer": "I have three books."},
                    {"words": ["favorite", "is", "My", "color", "blue", "."], "answer": "My favorite color is blue."},
                ],
            },
            "family": {
                "title_en": "Family & Daily Routine", "title_uz": "Oilaviy hayot",
                "emoji": "👨‍👩‍👧‍👦",
                "quiz": [
                    {"q": "'mother' in Uzbek?", "options": ["Ota", "Opa", "Ona", "Bola"], "answer": 2},
                    {"q": "Morning activity sentence?", "options": ["I go to bed", "I eat breakfast", "I watch TV at night", "I sleep late"], "answer": 1},
                    {"q": "Plural of 'child'?", "options": ["Childs", "Children", "Childes", "Childies"], "answer": 1},
                    {"q": "'I wake up at 7' means:", "options": ["Men 7 da uxlayman", "Men 7 da turaman", "Men 7 da ovqatlanaman", "Men 7 da ishlayman"], "answer": 1},
                    {"q": "Father's father?", "options": ["Uncle", "Cousin", "Grandfather", "Brother"], "answer": 2},
                ],
                "word_match": [("Father", "Ota"), ("Mother", "Ona"), ("Brother", "Aka"), ("Sister", "Opa"), ("Wake up", "Uyg'onmoq")],
                "sentence_build": [
                    {"words": ["is", "This", "my", "family", "."], "answer": "This is my family."},
                    {"words": ["I", "up", "wake", "at", "7", "o'clock", "."], "answer": "I wake up at 7 o'clock."},
                ],
            },
        },
    },
    "A2": {
        "title_en": "Elementary", "title_uz": "Elementar",
        "xp_required": 300,
        "topics": {
            "food": {
                "title_en": "Food & Restaurant", "title_uz": "Ovqatlar",
                "emoji": "🍕",
                "quiz": [
                    {"q": "Order food phrase?", "options": ["I want eating", "I would like to order please", "Give me food", "Food want I"], "answer": 1},
                    {"q": "'go'sht' in English?", "options": ["Fish", "Meat", "Chicken", "Bread"], "answer": 1},
                    {"q": "Which is vegetable?", "options": ["Apple", "Banana", "Carrot", "Milk"], "answer": 2},
                    {"q": "'Can I have the bill?' means:", "options": ["Hisobni so'rayapman", "Ovqat buyurtma", "Suv istayman", "Shifokorga boraman"], "answer": 0},
                    {"q": "Hot drink?", "options": ["Juice", "Coffee", "Cola", "Water"], "answer": 1},
                ],
                "word_match": [("Bread", "Non"), ("Water", "Suv"), ("Chicken", "Tovuq"), ("Rice", "Guruch"), ("Fruit", "Mevalar")],
                "sentence_build": [
                    {"words": ["I", "like", "eat", "to", "pizza", "."], "answer": "I like to eat pizza."},
                    {"words": ["please", "have", "I", "bill", "can", "the", ",", "?"], "answer": "Can I have the bill, please?"},
                ],
            },
            "travel": {
                "title_en": "Travel & Directions", "title_uz": "Sayohat",
                "emoji": "✈️",
                "quiz": [
                    {"q": "Ask for directions?", "options": ["Where is station?", "Go station where?", "Station is where?", "The station where is?"], "answer": 0},
                    {"q": "'Turn left' in Uzbek?", "options": ["O'ngga buril", "To'g'riga boring", "Chapga buril", "Orqaga qayt"], "answer": 2},
                    {"q": "Mode of transport?", "options": ["School", "Bus", "Hospital", "Library"], "answer": 1},
                    {"q": "'I need a ticket to London' means:", "options": ["Chipta kerak", "Londonnikiman", "Londonni yoqtiraman", "Londonda yashayman"], "answer": 0},
                    {"q": "'straight ahead' means:", "options": ["O'ngga", "Chapga", "To'g'riga boring", "Orqaga"], "answer": 2},
                ],
                "word_match": [("Airport", "Aeroport"), ("Hotel", "Mehmonxona"), ("Turn left", "Chapga buril"), ("Turn right", "O'ngga buril"), ("Ticket", "Chipta")],
                "sentence_build": [
                    {"words": ["is", "the", "Where", "station", "?"], "answer": "Where is the station?"},
                    {"words": ["I", "a", "taxi", "need", "."], "answer": "I need a taxi."},
                ],
            },
            "shopping": {
                "title_en": "Shopping & Clothes", "title_uz": "Sotib olish",
                "emoji": "🛍️",
                "quiz": [
                    {"q": "'How much?' in Uzbek?", "options": ["Bu nima?", "Narxi qancha?", "Bu qayerda?", "Bu nima uchun?"], "answer": 1},
                    {"q": "Piece of clothing?", "options": ["Apple", "T-shirt", "Chair", "Pen"], "answer": 1},
                    {"q": "'Can I try this on?' means:", "options": ["Olish", "Sinab ko'rish", "Yoqtirish", "Qaytarish"], "answer": 1},
                    {"q": "Buy groceries where?", "options": ["Pharmacy", "Supermarket", "Bank", "Post office"], "answer": 1},
                    {"q": "'kurtka' in English?", "options": ["Shirt", "Pants", "Jacket", "Shoes"], "answer": 2},
                ],
                "word_match": [("Shirt", "Ko'ylak"), ("Pants", "Shim"), ("Shoes", "Oyoq kiyim"), ("Expensive", "Qimmat"), ("Cheap", "Arzon")],
                "sentence_build": [
                    {"words": ["much", "How", "this", "is", "?"], "answer": "How much is this?"},
                    {"words": ["on", "try", "this", "can", "I", "?"], "answer": "Can I try this on?"},
                ],
            },
        },
    },
    "B1": {
        "title_en": "Intermediate", "title_uz": "O'rta",
        "xp_required": 900,
        "topics": {
            "health": {
                "title_en": "Health & Body", "title_uz": "Salomatlik",
                "emoji": "🏥",
                "quiz": [
                    {"q": "Say at doctor?", "options": ["I have a headache", "I have head pain", "My head is paining", "Head I have ache"], "answer": 0},
                    {"q": "See with?", "options": ["Ear", "Nose", "Eye", "Mouth"], "answer": 2},
                    {"q": "'Take medicine twice a day' means:", "options": ["Kuniga 1 marta", "Kuniga 2 marta", "Kechasi", "Ishlamaydi"], "answer": 1},
                    {"q": "'stomachache' means:", "options": ["Bosh og'rig'i", "Tish og'rig'i", "Qorin og'rig'i", "Tomon og'rig'i"], "answer": 2},
                    {"q": "Healthy habit?", "options": ["Smoking", "Exercising", "Sleep 3 hours", "Fast food only"], "answer": 1},
                ],
                "word_match": [("Headache", "Bosh og'rig'i"), ("Fever", "Isitma"), ("Medicine", "Dori"), ("Doctor", "Shifokor"), ("Healthy", "Sog'lom")],
                "sentence_build": [
                    {"words": ["should", "You", "doctor", "a", "see", "."], "answer": "You should see a doctor."},
                ],
            },
            "work": {
                "title_en": "Work & Career", "title_uz": "Ish va kasb",
                "emoji": "💼",
                "quiz": [
                    {"q": "'resume' in Uzbek?", "options": ["Xat", "Rezyume", "Shartnoma", "Maosh"], "answer": 1},
                    {"q": "Correct sentence?", "options": ["I am work", "I working", "I work in a bank", "I does work"], "answer": 2},
                    {"q": "'What are qualifications?' means:", "options": ["Ismingiz nima?", "Yoshingiz?", "Ma'lumotingiz nima?", "Qayerda yashaysiz?"], "answer": 2},
                    {"q": "Which is profession?", "options": ["Teacher", "Student", "Child", "Friend"], "answer": 0},
                    {"q": "'salary' means?", "options": ["Vaqt", "Joy", "Maosh", "Dam olish"], "answer": 2},
                ],
                "word_match": [("Job", "Ish"), ("Salary", "Maosh"), ("Experience", "Tajriba"), ("Interview", "Intervyu"), ("Colleague", "Hamkasb")],
                "sentence_build": [
                    {"words": ["for", "I", "applied", "a", "new", "job", "."], "answer": "I applied for a new job."},
                ],
            },
            "environment": {
                "title_en": "Environment & Nature", "title_uz": "Atrof-muhit",
                "emoji": "🌿",
                "quiz": [
                    {"q": "Which recycles?", "options": ["Throw away", "Recycle plastic", "Burn garbage", "Don't care"], "answer": 1},
                    {"q": "'global warming' in Uzbek?", "options": ["Sovish", "Isish", "Yomg'ir", "Shamol"], "answer": 1},
                    {"q": "Renewable energy?", "options": ["Coal", "Oil", "Solar power", "Gas"], "answer": 2},
                    {"q": "Air pollution cause?", "options": ["Trees", "Factory emissions", "Walking", "Solar panels"], "answer": 1},
                ],
                "word_match": [("Environment", "Atrof-muhit"), ("Pollution", "Ifloslanish"), ("Recycle", "Qayta ishlash"), ("Climate", "Iqlim")],
                "sentence_build": [
                    {"words": ["protect", "We", "the", "must", "environment", "."], "answer": "We must protect the environment."},
                ],
            },
        },
    },
    "B2": {
        "title_en": "Upper Intermediate", "title_uz": "Yuqori o'rta",
        "xp_required": 1800,
        "topics": {
            "technology": {
                "title_en": "Technology & Internet", "title_uz": "Texnologiya",
                "emoji": "💻",
                "quiz": [
                    {"q": "Correct grammar?", "options": ["Technology have", "Technology has changed", "Technology changing", "Technology changed we lives"], "answer": 1},
                    {"q": "'Artificial intelligence' refers to?", "options": ["Human thinking", "Computer simulating intelligence", "Robot", "Internet speed"], "answer": 1},
                    {"q": "What is 'smartphone'?", "options": ["Intelligent phone", "Advanced mobile phone", "Smart people phone", "Computer"], "answer": 1},
                    {"q": "Remote work benefit?", "options": ["Long commute", "Flexible schedule", "More meetings", "Higher costs"], "answer": 1},
                ],
                "word_match": [("Software", "Dasturiy ta'minot"), ("Database", "Ma'lumotlar bazasi"), ("Download", "Yuklab olish"), ("Password", "Parol")],
                "sentence_build": [
                    {"words": ["has", "The", "internet", "transformed", "the", "world", "."], "answer": "The internet has transformed the world."},
                ],
            },
            "culture": {
                "title_en": "Culture & Society", "title_uz": "Madaniyat",
                "emoji": "🌍",
                "quiz": [
                    {"q": "'Cultural diversity' means?", "options": ["One culture", "Multiple cultures", "Only traditional", "Not important"], "answer": 1},
                    {"q": "Correct sentence?", "options": ["Traditions is", "Tradition are", "Traditions are", "Traditions is being"], "answer": 2},
                    {"q": "What is 'stereotype'?", "options": ["Music type", "Oversimplified group image", "Celebration", "Social platform"], "answer": 1},
                ],
                "word_match": [("Tradition", "An'ana"), ("Custom", "Odat"), ("Heritage", "Meros"), ("Society", "Jamiyat"), ("Festival", "Bayram")],
                "sentence_build": [
                    {"words": ["respect", "should", "We", "all", "cultures", "."], "answer": "We should respect all cultures."},
                ],
            },
            "science": {
                "title_en": "Science & Education", "title_uz": "Fan va ta'lim",
                "emoji": "🔬",
                "quiz": [
                    {"q": "'hypothesis' means?", "options": ["Proven fact", "Proposed explanation", "Conclusion", "Experiment"], "answer": 1},
                    {"q": "Correct sentence?", "options": ["The scientist have", "Scientists has", "Scientists have discovered", "Scientist has discover"], "answer": 2},
                    {"q": "Scientific method?", "options": ["Guessing", "Systematic investigation", "Memorizing", "Only reading"], "answer": 1},
                ],
                "word_match": [("Experiment", "Tajriba"), ("Discovery", "Kashfiyot"), ("Research", "Tadqiqot"), ("Theory", "Nazariya")],
                "sentence_build": [
                    {"words": ["conducted", "The", "experiment", "was", "successfully", "."], "answer": "The experiment was conducted successfully."},
                ],
            },
        },
    },
    "C1": {
        "title_en": "Advanced", "title_uz": "Yuqori darajali",
        "xp_required": 3000,
        "topics": {
            "academic_writing": {
                "title_en": "Academic Writing", "title_uz": "Ilmiy yozish",
                "emoji": "📝",
                "quiz": [
                    {"q": "Which is more formal?", "options": ["I think", "It is argued that", "You know", "Basically"], "answer": 1},
                    {"q": "'Furthermore' is similar to:", "options": ["But", "In addition", "However", "Although"], "answer": 1},
                    {"q": "Academic essay structure?", "options": ["Intro-Body-Conclusion", "Random", "Only conclusion", "Question-answer"], "answer": 0},
                    {"q": "Formal word for 'get'?", "options": ["Obtain", "Grab", "Take", "Catch"], "answer": 0},
                    {"q": "'Nevertheless' means:", "options": ["Therefore", "However", "Because", "So"], "answer": 1},
                ],
                "word_match": [("Therefore", "Shuning uchun"), ("Furthermore", "Bundan tashqari"), ("Nevertheless", "Bunga qaramay"), ("Consequently", "Oqibatda"), ("Significant", "Muhim")],
                "sentence_build": [
                    {"words": ["argued", "is", "It", "that", "education", "is", "essential", "."], "answer": "It is argued that education is essential."},
                ],
            },
            "idioms_advanced": {
                "title_en": "Advanced Idioms", "title_uz": "Murakkab iboralar",
                "emoji": "🎯",
                "quiz": [
                    {"q": "'Break a leg' means:", "options": ["Get hurt", "Good luck", "Stop", "Run fast"], "answer": 1},
                    {"q": "'Hit the nail on the head' means:", "options": ["Build something", "Be exactly right", "Carpentry", "Make a mistake"], "answer": 1},
                    {"q": "'Bite the bullet' means:", "options": ["Eat something", "Face difficulty bravely", "Be angry", "Be quiet"], "answer": 1},
                    {"q": "'The ball is in your court' means:", "options": ["Play sports", "It's your decision now", "Go to court", "Watch a game"], "answer": 1},
                ],
                "word_match": [("Break a leg", "Omad tilash"), ("Piece of cake", "Juda oson"), ("Under the weather", "Kasal"), ("Once in a blue moon", "Juda kam"), ("Burn the midnight oil", "Kechgacha ishlash")],
                "sentence_build": [
                    {"words": ["is", "This", "a", "of", "piece", "cake", "."], "answer": "This is a piece of cake."},
                ],
            },
            "conditional_advanced": {
                "title_en": "Advanced Conditionals", "title_uz": "Murakkab shart gaplar",
                "emoji": "🔗",
                "quiz": [
                    {"q": "Mixed conditional: If I __ harder, I would have passed.", "options": ["study", "studied", "had studied", "would study"], "answer": 2},
                    {"q": "Inversion: Had I known, I __ differently.", "options": ["would act", "would have acted", "act", "acted"], "answer": 1},
                    {"q": "'Were she to arrive early, she...'", "options": ["is formal", "uses subjunctive", "is wrong", "is casual"], "answer": 1},
                    {"q": "'But for your help, I __ failed.'", "options": ["will", "would have", "have", "had"], "answer": 1},
                ],
                "word_match": [("Mixed conditional", "Aralash shart"), ("Inversion", "Teskari tartib"), ("Subjunctive", "Shart ko'rinishi"), ("Concessive clause", "Qo'shimcha shart")],
                "sentence_build": [
                    {"words": ["I", "had", "known", ",", "would", "have", "I", "helped", "."], "answer": "Had I known, I would have helped."},
                ],
            },
        },
    },
    "C2": {
        "title_en": "Mastery", "title_uz": "Mukammal",
        "xp_required": 5000,
        "topics": {
            "literature": {
                "title_en": "Literature & Poetry", "title_uz": "Adabiyot",
                "emoji": "📚",
                "quiz": [
                    {"q": "'Shakespeare' is known for:", "options": ["Paintings", "Plays and sonnets", "Science", "Music"], "answer": 1},
                    {"q": "'Metaphor' is:", "options": ["Direct comparison", "Implied comparison", "Exaggeration", "Understatement"], "answer": 1},
                    {"q": "'Alliteration' means:", "options": ["Repetition of sounds", "Repetition of meaning", "Opposite meaning", "Similar meaning"], "answer": 0},
                    {"q": "'Protagonist' is:", "options": ["Villain", "Main character", "Setting", "Theme"], "answer": 1},
                ],
                "word_match": [("Metaphor", "Metafora"), ("Simile", "Taqqoslash"), ("Irony", "Aksincha"), ("Allegory", "Majaziy"), ("Protagonist", "Bosh qahramon")],
                "sentence_build": [
                    {"words": ["is", "a", "metaphor", "This", "of", "life", "."], "answer": "This is a metaphor of life."},
                ],
            },
            "formal_register": {
                "title_en": "Formal Register", "title_uz": "Rasmiy til",
                "emoji": "🏛️",
                "quiz": [
                    {"q": "Formal for 'a lot of'?", "options": ["Numerous", "A great deal of", "Many much", "Lots of"], "answer": 1},
                    {"q": "'I am writing to inquire about...'", "options": ["Formal", "Informal", "Slang", "Wrong"], "answer": 0},
                    {"q": "Passive voice in formal writing:", "options": ["Never used", "Commonly used", "Is incorrect", "Only in speech"], "answer": 1},
                ],
                "word_match": [("Inquire", "So'rash"), ("Regarding", "Haqida"), ("Subsequently", "Keyinroq"), ("Nevertheless", "Bunga qaramay"), ("Furthermore", "Bundan tashqari")],
                "sentence_build": [
                    {"words": ["I", "am", "writing", "to", "inquire", "regarding", "the", "matter", "."], "answer": "I am writing to inquire regarding the matter."},
                ],
            },
            "nuanced_vocab": {
                "title_en": "Nuanced Vocabulary", "title_uz": "Nozik lug'at",
                "emoji": "🧠",
                "quiz": [
                    {"q": "Difference: 'affect' vs 'effect'?", "options": ["Same", "Affect=verb, Effect=noun", "Effect=verb, Affect=noun", "Both nouns"], "answer": 1},
                    {"q": "'Comprise' means:", "options": ["Exclude", "Consist of", "Separate", "Compare"], "answer": 1},
                    {"q": "'Mitigate' means:", "options": ["Worsen", "Make less severe", "Ignore", "Create"], "answer": 1},
                ],
                "word_match": [("Affect", "Ta'sir qilmoq"), ("Effect", "Natija"), ("Comprise", "Tashkil qilmoq"), ("Mitigate", "Yengillashtirmoq"), ("Elucidate", "Tushuntirmoq")],
                "sentence_build": [
                    {"words": ["measures", "were", "taken", "to", "mitigate", "the", "impact", "."], "answer": "Measures were taken to mitigate the impact."},
                ],
            },
        },
    },
    "IELTS": {
        "title_en": "IELTS Preparation", "title_uz": "IELTS Tayyorgarlik",
        "xp_required": 2500,
        "topics": {
            "ielts_reading": {
                "title_en": "IELTS Reading", "title_uz": "IELTS O'qish",
                "emoji": "📖",
                "quiz": [
                    {"q": "IELTS Reading has how many passages?", "options": ["2", "3", "4", "5"], "answer": 1},
                    {"q": "Total time for Reading section?", "options": ["30 min", "60 min", "90 min", "45 min"], "answer": 1},
                    {"q": "Types of IELTS Reading questions?", "options": ["Only MCQ", "Multiple types", "Only True/False", "Only matching"], "answer": 1},
                    {"q": "Skimming means:", "options": ["Reading every word", "Quick overview", "Deep analysis", "Memorizing"], "answer": 1},
                    {"q": "'NOT GIVEN' means:", "options": ["False", "Not mentioned in text", "True", "Maybe"], "answer": 1},
                ],
                "word_match": [("Skimming", "Sirtaki o'qish"), ("Scanning", "Qidirish"), ("Heading", "Sarlavha"), ("Matching", "Moslashtirish"), ("True/False/NG", "To'g'ri/Noto'g'ri/Berilmagan")],
                "sentence_build": [
                    {"words": ["should", "You", "skim", "the", "passage", "first", "."], "answer": "You should skim the passage first."},
                ],
            },
            "ielts_writing": {
                "title_en": "IELTS Writing", "title_uz": "IELTS Yozish",
                "emoji": "✍️",
                "quiz": [
                    {"q": "IELTS Writing Task 1 is:", "options": ["Essay", "Graph/Table description", "Letter", "Story"], "answer": 1},
                    {"q": "Word count for Task 2?", "options": ["150+", "200+", "250+", "100+"], "answer": 2},
                    {"q": "Band descriptors assess:", "options": ["Only grammar", "4 criteria", "Only vocabulary", "Only ideas"], "answer": 1},
                    {"q": "Formal linking word?", "options": ["Like", "Moreover", "Stuff", "Thing"], "answer": 1},
                ],
                "word_match": [("Task Achievement", "Vazifani bajarish"), ("Coherence", "Mantiqiy bog'liqlik"), ("Lexical Resource", "Lug'at resursi"), ("Grammatical Range", "Grammatik ko'lam"), ("Band 9", "Eng yuqori ball")],
                "sentence_build": [
                    {"words": ["It", "is", "widely", "argued", "that", "technology", "impacts", "society", "."], "answer": "It is widely argued that technology impacts society."},
                ],
            },
            "ielts_listening": {
                "title_en": "IELTS Listening", "title_uz": "IELTS Tinglash",
                "emoji": "🎧",
                "quiz": [
                    {"q": "IELTS Listening has how many sections?", "options": ["2", "3", "4", "5"], "answer": 2},
                    {"q": "Audio is played:", "options": ["Once", "Twice", "Three times", "Unlimited"], "answer": 0},
                    {"q": "Section 1 is usually:", "options": ["Academic lecture", "Everyday conversation", "News report", "Debate"], "answer": 1},
                    {"q": "Spelling mistakes:", "options": ["Are ignored", "Lose marks", "Are fine", "Don't matter"], "answer": 1},
                ],
                "word_match": [("Section", "Bo'lim"), ("Multiple choice", "Ko'p tanlov"), ("Map labeling", "Xaritani belgilash"), ("Note completion", "Eslatmani to'ldirish"), ("Speaker", "Ma'ruzachi")],
                "sentence_build": [
                    {"words": ["listen", "should", "You", "carefully", "to", "the", "instructions", "."], "answer": "You should listen carefully to the instructions."},
                ],
            },
        },
    },
    "SAT": {
        "title_en": "SAT Preparation", "title_uz": "SAT Tayyorgarlik",
        "xp_required": 3500,
        "topics": {
            "sat_grammar": {
                "title_en": "SAT Grammar", "title_uz": "SAT Grammatika",
                "emoji": "📐",
                "quiz": [
                    {"q": "SAT Writing section focuses on:", "options": ["Creative writing", "Grammar and usage", "Handwriting", "Spelling only"], "answer": 1},
                    {"q": "'Their going to the store' - error?", "options": ["No error", "'Their' should be 'There'", "'Going' wrong", "'Store' wrong"], "answer": 1},
                    {"q": "Subject-verb agreement:", "options": ["Don't matter", "Must match", "Are optional", "Only in past tense"], "answer": 1},
                    {"q": "Comma splice is:", "options": ["Correct usage", "Two independent clauses joined by comma only", "Missing comma", "Extra comma"], "answer": 1},
                ],
                "word_match": [("Comma splice", "Vergul xatosi"), ("Run-on", "Uzluksiz gap"), ("Parallelism", "Parallelizm"), ("Modifier", "Modifikator"), ("Clause", "Gap bo'lagi")],
                "sentence_build": [
                    {"words": ["The", "students", "are", "studying", "for", "the", "exam", "."], "answer": "The students are studying for the exam."},
                ],
            },
            "sat_math_vocab": {
                "title_en": "SAT Math Vocabulary", "title_uz": "SAT Matematika terminlari",
                "emoji": "🔢",
                "quiz": [
                    {"q": "'Integer' means:", "options": ["Decimal", "Whole number", "Fraction", "Negative only"], "answer": 1},
                    {"q": "'Equation' is:", "options": ["Shape", "Mathematical statement with equality", "Graph", "Number"], "answer": 1},
                    {"q": "'Isosceles triangle' has:", "options": ["3 equal sides", "2 equal sides", "No equal sides", "4 sides"], "answer": 1},
                    {"q": "'Radius' of a circle:", "options": ["Diameter", "Half of diameter", "Circumference", "Area"], "answer": 1},
                ],
                "word_match": [("Integer", "Butun son"), ("Equation", "Tenglama"), ("Variable", "O'zgaruvchi"), ("Coefficient", "Koeffitsient"), ("Radius", "Radius")],
                "sentence_build": [
                    {"words": ["The", "equation", "has", "two", "variables", "."], "answer": "The equation has two variables."},
                ],
            },
            "sat_reading": {
                "title_en": "SAT Reading", "title_uz": "SAT O'qish",
                "emoji": "📖",
                "quiz": [
                    {"q": "SAT Evidence-Based Reading has:", "options": ["Only fiction", "5 passages", "1 passage", "Only science"], "answer": 1},
                    {"q": "Passage types include:", "options": ["Only stories", "Multiple types", "Only history", "Only poems"], "answer": 1},
                    {"q": "'Inference' question asks:", "options": ["Direct fact", "What can be concluded", "Author's name", "Word count"], "answer": 1},
                ],
                "word_match": [("Inference", "Xulosa chiqarish"), ("Evidence", "Dalil"), ("Context", "Kontekst"), ("Passage", "Matn"), ("Vocabulary", "Lug'at")],
                "sentence_build": [
                    {"words": ["The", "passage", "suggests", "that", "the", "author", "believes", "."], "answer": "The passage suggests that the author believes."},
                ],
            },
        },
    },
}


# ─── Helper: get game title in user's language ─────────────────────────────
def _level_title(level_data: dict, lang: str) -> str:
    if lang == "uz":
        return level_data.get("title_uz", level_data["title_en"])
    return level_data["title_en"]


def _topic_title(topic_data: dict, lang: str) -> str:
    if lang == "uz":
        return topic_data.get("title_uz", topic_data["title_en"])
    return topic_data["title_en"]


# ─── 1. Games Menu: Show level selection ───────────────────────────────────
async def handle_games_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show game level selection with XP info."""
    user_id = update.effective_user.id
    lang = await get_user_lang(user_id)
    t = lambda k, **kw: get_trans(lang, k, **kw)

    progress = await get_game_progress(user_id)
    xp = progress.get("xp", 0)
    completed = progress.get("completed_topics", [])

    # Build level buttons
    keyboard = []
    for level_key in ["A1", "A2", "B1", "B2", "C1", "C2", "IELTS", "SAT"]:
        level = GAME_LEVELS[level_key]
        title = _level_title(level, lang)
        xp_req = level["xp_required"]
        # Count completed topics in this level
        done = sum(1 for tk in level["topics"] if f"{level_key}_{tk}" in completed)
        total = len(level["topics"])
        icon = "🔓" if xp >= xp_req else "🔒"
        keyboard.append([InlineKeyboardButton(
            f"{icon} {level_key} - {title} ({done}/{total}) [{xp_req} XP]",
            callback_data=f"game_level_{level_key}"
        )])

    back_btn = InlineKeyboardButton(f"◀️ {t('btn_main_menu')}", callback_data="game_back")
    keyboard.append([back_btn])

    total_completed = len(completed)
    msg = (
        f"🎮 *{t('games_title')}*\n\n"
        f"⭐ XP: *{xp}*\n"
        f"✅ {t('games_completed')}: *{total_completed}/30*\n\n"
        f"{t('games_select_level')}:"
    )
    await update.message.reply_text(
        msg, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ─── 2. Level Topics: Show topics for a level ──────────────────────────────
async def handle_games_level(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              level_key: str) -> None:
    """Show topics for a specific level."""
    user_id = update.effective_user.id
    lang = await get_user_lang(user_id)
    t = lambda k, **kw: get_trans(lang, k, **kw)

    level = GAME_LEVELS.get(level_key)
    if not level:
        await update.callback_query.message.reply_text("❌ Level not found.")
        return

    progress = await get_game_progress(user_id)
    xp = progress.get("xp", 0)
    completed = progress.get("completed_topics", [])

    if xp < level["xp_required"]:
        await update.callback_query.message.reply_text(
            f"🔒 {t('games_locked', required=level['xp_required'], current=xp)}"
        )
        return

    title = _level_title(level, lang)
    keyboard = []
    for topic_key, topic_data in level["topics"].items():
        topic_id = f"{level_key}_{topic_key}"
        is_done = topic_id in completed
        icon = "✅" if is_done else topic_data["emoji"]
        t_title = _topic_title(topic_data, lang)
        keyboard.append([InlineKeyboardButton(
            f"{icon} {t_title}",
            callback_data=f"game_topic_{level_key}_{topic_key}"
        )])

    back_btn = InlineKeyboardButton(f"◀️ {t('games_back_levels')}", callback_data="game_menu")
    keyboard.append([back_btn])

    msg = (
        f"📚 *{level_key} - {title}*\n\n"
        f"{t('games_select_topic')}:"
    )
    await update.callback_query.message.reply_text(
        msg, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ─── 3. Game Mode Selection ────────────────────────────────────────────────
async def handle_games_topic(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              level_key: str, topic_key: str) -> None:
    """Show game mode selection for a topic."""
    user_id = update.effective_user.id
    lang = await get_user_lang(user_id)
    t = lambda k, **kw: get_trans(lang, k, **kw)

    level = GAME_LEVELS.get(level_key)
    topic = level["topics"].get(topic_key) if level else None
    if not topic:
        return

    title = _topic_title(topic, lang)
    keyboard = [
        [
            InlineKeyboardButton(f"📝 {t('games_mode_quiz')}", callback_data=f"game_quiz_{level_key}_{topic_key}"),
            InlineKeyboardButton(f"🔗 {t('games_mode_word')}", callback_data=f"game_word_{level_key}_{topic_key}"),
        ],
        [
            InlineKeyboardButton(f"🏗️ {t('games_mode_sentence')}", callback_data=f"game_sentence_{level_key}_{topic_key}"),
        ],
        [
            InlineKeyboardButton(f"◀️ {t('games_back_topics')}", callback_data=f"game_level_{level_key}"),
        ],
    ]

    msg = (
        f"{topic['emoji']} *{title}*\n\n"
        f"{t('games_select_mode')}:"
    )
    await update.callback_query.message.reply_text(
        msg, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ─── 4. Quiz Game ──────────────────────────────────────────────────────────
async def handle_games_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              level_key: str, topic_key: str) -> None:
    """Interactive quiz with inline buttons."""
    user_id = update.effective_user.id
    lang = await get_user_lang(user_id)
    t = lambda k, **kw: get_trans(lang, k, **kw)

    level = GAME_LEVELS.get(level_key)
    topic = level["topics"].get(topic_key) if level else None
    if not topic:
        return

    quiz_questions = topic.get("quiz", [])
    if not quiz_questions:
        await update.callback_query.message.reply_text("❌ No quiz questions available.")
        return

    # Initialize quiz state
    context.user_data['game_quiz'] = {
        "level": level_key,
        "topic": topic_key,
        "questions": quiz_questions,
        "current": 0,
        "score": 0,
    }

    await _send_quiz_question(update, context, lang, t)


async def _send_quiz_question(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                lang: str, t) -> None:
    """Send current quiz question."""
    quiz_data = context.user_data.get('game_quiz')
    if not quiz_data:
        return

    idx = quiz_data["current"]
    questions = quiz_data["questions"]

    if idx >= len(questions):
        await _finish_quiz(update, context, lang, t)
        return

    q = questions[idx]
    keyboard = []
    row = []
    for i, opt in enumerate(q["options"]):
        row.append(InlineKeyboardButton(
            opt, callback_data=f"game_ans_{i}"
        ))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    msg = (
        f"📝 {t('games_quiz_question')} *{idx + 1}/{len(questions)}*\n\n"
        f"❓ {q['q']}"
    )
    sent = await update.callback_query.message.reply_text(
        msg, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data['game_quiz_msg'] = sent.message_id


async def _handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                answer_idx: int) -> None:
    """Process quiz answer."""
    quiz_data = context.user_data.get('game_quiz')
    if not quiz_data:
        return

    user_id = update.effective_user.id
    lang = await get_user_lang(user_id)
    t = lambda k, **kw: get_trans(lang, k, **kw)

    q = quiz_data["questions"][quiz_data["current"]]
    correct = q["answer"]
    is_correct = (answer_idx == correct)

    if is_correct:
        quiz_data["score"] += 1
        result_text = f"✅ {t('games_correct')}!"
    else:
        result_text = f"❌ {t('games_wrong')}. {t('games_correct_answer')}: {q['options'][correct]}"

    quiz_data["current"] += 1
    remaining = len(quiz_data["questions"]) - quiz_data["current"]

    await update.callback_query.message.reply_text(result_text)

    if quiz_data["current"] >= len(quiz_data["questions"]):
        await _finish_quiz(update, context, lang, t)
    else:
        # Auto-send next question after a short delay
        import asyncio
        await asyncio.sleep(0.5)
        await _send_quiz_question(update, context, lang, t)


async def _finish_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE,
                         lang: str, t) -> None:
    """Finish quiz and award XP."""
    quiz_data = context.user_data.get('game_quiz')
    if not quiz_data:
        return

    user_id = update.effective_user.id
    score = quiz_data["score"]
    total = len(quiz_data["questions"])

    xp_earned = score * 20
    bonus = 50 if score == total else 0
    total_xp = xp_earned + bonus

    # Save progress
    progress = await get_game_progress(user_id)
    current_xp = progress.get("xp", 0)
    completed = progress.get("completed_topics", [])
    topic_id = f"{quiz_data['level']}_{quiz_data['topic']}"

    if topic_id not in completed:
        completed.append(topic_id)

    await save_game_progress(user_id, current_xp + total_xp, completed)

    pct = (score / total * 100) if total > 0 else 0
    emoji = "🏆" if pct == 100 else "🎉" if pct >= 80 else "👍" if pct >= 60 else "💪"
    comment = "Excellent!" if pct == 100 else "Great job!" if pct >= 80 else "Good effort!" if pct >= 60 else "Keep practicing!"

    msg = (
        f"{emoji} *{t('games_quiz_done')}*\n\n"
        f"📊 {t('games_result')}: *{score}/{total}* ({pct:.0f}%)\n"
        f"⭐ +{xp_earned} XP"
    )
    if bonus:
        msg += f"\n🎁 +{bonus} XP {t('games_bonus')}"

    msg += f"\n\n💡 {comment}"
    msg += f"\n\n⭐ {t('games_total_xp')}: *{current_xp + total_xp}*"

    keyboard = [[InlineKeyboardButton(
        f"▶️ {t('games_play_again')}",
        callback_data=f"game_topic_{quiz_data['level']}_{quiz_data['topic']}"
    )],
    [InlineKeyboardButton(
        f"◀️ {t('games_back_topics')}",
        callback_data=f"game_level_{quiz_data['level']}"
    )]]

    await update.callback_query.message.reply_text(
        msg, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data.pop('game_quiz', None)


# ─── 5. Word Match Game ───────────────────────────────────────────────────
async def handle_games_word_match(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                    level_key: str, topic_key: str) -> None:
    """Word matching game."""
    user_id = update.effective_user.id
    lang = await get_user_lang(user_id)
    t = lambda k, **kw: get_trans(lang, k, **kw)

    level = GAME_LEVELS.get(level_key)
    topic = level["topics"].get(topic_key) if level else None
    if not topic:
        return

    pairs = topic.get("word_match", [])
    if not pairs:
        await update.callback_query.message.reply_text("❌ No word pairs available.")
        return

    # Shuffle translations for options
    translations = [p[1] for p in pairs]
    random.shuffle(translations)

    context.user_data['game_word'] = {
        "level": level_key,
        "topic": topic_key,
        "pairs": pairs,
        "translations": translations,
        "matched": [],
        "score": 0,
        "current_en": pairs[0][0],
        "current_idx": 0,
    }

    await _send_word_match_round(update, context, lang, t)


async def _send_word_match_round(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   lang: str, t) -> None:
    """Send current word match round."""
    word_data = context.user_data.get('game_word')
    if not word_data:
        return

    pairs = word_data["pairs"]
    matched = word_data["matched"]
    translations = word_data["translations"]

    # Find next unmatched English word
    while word_data["current_idx"] < len(pairs):
        en_word = pairs[word_data["current_idx"]][0]
        uz_word = pairs[word_data["current_idx"]][1]
        if f"{en_word}|{uz_word}" not in matched:
            word_data["current_en"] = en_word
            word_data["current_uz"] = uz_word
            break
        word_data["current_idx"] += 1
    else:
        # All matched
        await _finish_word_match(update, context, lang, t)
        return

    en_word = word_data["current_en"]

    # Build keyboard with remaining unmatched translations
    keyboard = []
    row = []
    remaining_trans = [tr for tr in translations if tr not in matched]
    random.shuffle(remaining_trans)
    for tr in remaining_trans:
        row.append(InlineKeyboardButton(tr, callback_data=f"game_wmatch_{tr}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # Show matched so far
    matched_list = "\n".join(f"  ✅ {m.split('|')[0]} — {m.split('|')[1]}" for m in matched) if matched else ""
    matched_section = f"\n\n✅ {t('games_matched')}:\n{matched_list}" if matched_list else ""

    msg = (
        f"🔗 *{t('games_word_match_title')}*\n\n"
        f"🔤 *{en_word}* — {t('games_word_match_hint')}\n"
        f"{matched_section}"
    )
    await update.callback_query.message.reply_text(
        msg, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def _handle_word_match_answer(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                      answer: str) -> None:
    """Process word match answer."""
    word_data = context.user_data.get('game_word')
    if not word_data:
        return

    user_id = update.effective_user.id
    lang = await get_user_lang(user_id)
    t = lambda k, **kw: get_trans(lang, k, **kw)

    current_uz = word_data["current_uz"]
    if answer == current_uz:
        en_word = word_data["current_en"]
        word_data["matched"].append(f"{en_word}|{answer}")
        word_data["score"] += 1
        await update.callback_query.message.reply_text(
            f"✅ {t('games_correct')}! *{en_word}* = *{answer}*", parse_mode="Markdown"
        )
    else:
        await update.callback_query.message.reply_text(
            f"❌ {t('games_wrong')}. {t('games_try_again')}."
        )

    import asyncio
    await asyncio.sleep(0.5)
    await _send_word_match_round(update, context, lang, t)


async def _finish_word_match(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               lang: str, t) -> None:
    """Finish word match and award XP."""
    word_data = context.user_data.get('game_word')
    if not word_data:
        return

    user_id = update.effective_user.id
    score = word_data["score"]
    total = len(word_data["pairs"])
    xp_earned = score * 10

    progress = await get_game_progress(user_id)
    current_xp = progress.get("xp", 0)
    completed = progress.get("completed_topics", [])
    topic_id = f"{word_data['level']}_{word_data['topic']}"
    if topic_id not in completed:
        completed.append(topic_id)
    await save_game_progress(user_id, current_xp + xp_earned, completed)

    msg = (
        f"🏆 *{t('games_word_done')}*\n\n"
        f"📊 {t('games_result')}: *{score}/{total}*\n"
        f"⭐ +{xp_earned} XP\n\n"
        f"⭐ {t('games_total_xp')}: *{current_xp + xp_earned}*"
    )
    keyboard = [[InlineKeyboardButton(
        f"▶️ {t('games_play_again')}",
        callback_data=f"game_topic_{word_data['level']}_{word_data['topic']}"
    )],
    [InlineKeyboardButton(
        f"◀️ {t('games_back_topics')}",
        callback_data=f"game_level_{word_data['level']}"
    )]]

    await update.callback_query.message.reply_text(
        msg, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data.pop('game_word', None)


# ─── 6. Sentence Build Game ────────────────────────────────────────────────
async def handle_games_sentence(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                  level_key: str, topic_key: str) -> None:
    """Sentence building game."""
    user_id = update.effective_user.id
    lang = await get_user_lang(user_id)
    t = lambda k, **kw: get_trans(lang, k, **kw)

    level = GAME_LEVELS.get(level_key)
    topic = level["topics"].get(topic_key) if level else None
    if not topic:
        return

    sentences = topic.get("sentence_build", [])
    if not sentences:
        await update.callback_query.message.reply_text("❌ No sentence exercises available.")
        return

    # Shuffle words for first sentence
    first = sentences[0]
    shuffled = first["words"][:]
    random.shuffle(shuffled)

    context.user_data['game_sentence'] = {
        "level": level_key,
        "topic": topic_key,
        "sentences": sentences,
        "current": 0,
        "score": 0,
        "built": [],
        "shuffled": shuffled,
    }

    await _send_sentence_round(update, context, lang, t)


async def _send_sentence_round(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                 lang: str, t) -> None:
    """Send current sentence building round."""
    sent_data = context.user_data.get('game_sentence')
    if not sent_data:
        return

    idx = sent_data["current"]
    sentences = sent_data["sentences"]

    if idx >= len(sentences):
        await _finish_sentence(update, context, lang, t)
        return

    correct = sentences[idx]["answer"]
    built = sent_data["built"]
    shuffled = sent_data["shuffled"]

    # Build keyboard with remaining words
    remaining = [w for w in shuffled if w not in built]
    keyboard = []
    row = []
    for w in remaining:
        row.append(InlineKeyboardButton(w, callback_data=f"game_sbuild_{w}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # Show check button if words selected
    if built:
        keyboard.append([InlineKeyboardButton(
            f"✅ {t('games_check')}", callback_data="game_scheck"
        )])
        keyboard.append([InlineKeyboardButton(
            f"🗑 {t('games_clear')}", callback_data="game_sclear"
        )])

    built_str = " ".join(built)
    msg = (
        f"🏗️ *{t('games_sentence_title')}* ({idx + 1}/{len(sentences)})\n\n"
        f"📝 {t('games_built_sentence')}: *{built_str}*" if built else
        f"🏗️ *{t('games_sentence_title')}* ({idx + 1}/{len(sentences)})\n\n"
        f"📝 {t('games_tap_words')}:"
    )
    await update.callback_query.message.reply_text(
        msg, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def _handle_sentence_word(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                  word: str) -> None:
    """Handle word tap in sentence building."""
    sent_data = context.user_data.get('game_sentence')
    if not sent_data:
        return

    sent_data["built"].append(word)
    user_id = update.effective_user.id
    lang = await get_user_lang(user_id)
    t = lambda k, **kw: get_trans(lang, k, **kw)
    await _send_sentence_round(update, context, lang, t)


async def _handle_sentence_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check the built sentence."""
    sent_data = context.user_data.get('game_sentence')
    if not sent_data:
        return

    user_id = update.effective_user.id
    lang = await get_user_lang(user_id)
    t = lambda k, **kw: get_trans(lang, k, **kw)

    sentences = sent_data["sentences"]
    idx = sent_data["current"]
    correct = sentences[idx]["answer"]
    built_str = " ".join(sent_data["built"])

    if built_str == correct:
        sent_data["score"] += 1
        await update.callback_query.message.reply_text(
            f"✅ {t('games_correct')}! *{correct}*", parse_mode="Markdown"
        )
        sent_data["current"] += 1
        # Reset for next sentence
        if sent_data["current"] < len(sentences):
            next_sent = sentences[sent_data["current"]]
            shuffled = next_sent["words"][:]
            random.shuffle(shuffled)
            sent_data["built"] = []
            sent_data["shuffled"] = shuffled
        import asyncio
        await asyncio.sleep(0.5)
        await _send_sentence_round(update, context, lang, t)
    else:
        await update.callback_query.message.reply_text(
            f"❌ {t('games_wrong')}. {t('games_try_again')}.\n\n"
            f"💡 {t('games_hint')}: {correct[:3]}..."
        )


async def _handle_sentence_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear built sentence."""
    sent_data = context.user_data.get('game_sentence')
    if not sent_data:
        return
    sent_data["built"] = []
    user_id = update.effective_user.id
    lang = await get_user_lang(user_id)
    t = lambda k, **kw: get_trans(lang, k, **kw)
    await _send_sentence_round(update, context, lang, t)


async def _finish_sentence(update: Update, context: ContextTypes.DEFAULT_TYPE,
                             lang: str, t) -> None:
    """Finish sentence game and award XP."""
    sent_data = context.user_data.get('game_sentence')
    if not sent_data:
        return

    user_id = update.effective_user.id
    score = sent_data["score"]
    total = len(sent_data["sentences"])
    xp_earned = score * 15

    progress = await get_game_progress(user_id)
    current_xp = progress.get("xp", 0)
    completed = progress.get("completed_topics", [])
    topic_id = f"{sent_data['level']}_{sent_data['topic']}"
    if topic_id not in completed:
        completed.append(topic_id)
    await save_game_progress(user_id, current_xp + xp_earned, completed)

    msg = (
        f"🏆 *{t('games_sentence_done')}*\n\n"
        f"📊 {t('games_result')}: *{score}/{total}*\n"
        f"⭐ +{xp_earned} XP\n\n"
        f"⭐ {t('games_total_xp')}: *{current_xp + xp_earned}*"
    )
    keyboard = [[InlineKeyboardButton(
        f"▶️ {t('games_play_again')}",
        callback_data=f"game_topic_{sent_data['level']}_{sent_data['topic']}"
    )],
    [InlineKeyboardButton(
        f"◀️ {t('games_back_topics')}",
        callback_data=f"game_level_{sent_data['level']}"
    )]]

    await update.callback_query.message.reply_text(
        msg, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data.pop('game_sentence', None)


# ─── 7. Callback Router for Games ──────────────────────────────────────────
async def handle_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route all game-related callbacks."""
    query = update.callback_query
    await query.answer()
    data = query.data

    # Back to main menu
    if data == "game_back":
        return  # Let main callback handle it

    # Games menu
    if data == "game_menu":
        # Re-send games menu as a new message
        from bot.handlers.games import handle_games_menu
        # We need to simulate — use callback_query message
        class FakeUpdate:
            def __init__(self, orig, msg):
                self.effective_user = orig.from_user
                self.effective_chat = msg.chat
                self.message = msg
        fake = FakeUpdate(query, query.message)
        await handle_games_menu(fake, context)
        return

    # Level selection
    if data.startswith("game_level_"):
        level_key = data.replace("game_level_", "")
        await handle_games_level(update, context, level_key)
        return

    # Topic selection
    if data.startswith("game_topic_"):
        parts = data.replace("game_topic_", "").split("_", 1)
        if len(parts) == 2:
            await handle_games_topic(update, context, parts[0], parts[1])
        return

    # Quiz answer
    if data.startswith("game_ans_"):
        answer_idx = int(data.replace("game_ans_", ""))
        await _handle_quiz_answer(update, context, answer_idx)
        return

    # Quiz start
    if data.startswith("game_quiz_"):
        parts = data.replace("game_quiz_", "").split("_", 1)
        if len(parts) == 2:
            await handle_games_quiz(update, context, parts[0], parts[1])
        return

    # Word match answer
    if data.startswith("game_wmatch_"):
        answer = data.replace("game_wmatch_", "")
        await _handle_word_match_answer(update, context, answer)
        return

    # Word match start
    if data.startswith("game_word_"):
        parts = data.replace("game_word_", "").split("_", 1)
        if len(parts) == 2:
            await handle_games_word_match(update, context, parts[0], parts[1])
        return

    # Sentence build
    if data.startswith("game_sbuild_"):
        word = data.replace("game_sbuild_", "")
        await _handle_sentence_word(update, context, word)
        return

    if data == "game_scheck":
        await _handle_sentence_check(update, context)
        return

    if data == "game_sclear":
        await _handle_sentence_clear(update, context)
        return

    # Sentence start
    if data.startswith("game_sentence_"):
        parts = data.replace("game_sentence_", "").split("_", 1)
        if len(parts) == 2:
            await handle_games_sentence(update, context, parts[0], parts[1])
        return
