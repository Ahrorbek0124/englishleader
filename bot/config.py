import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8631729300:AAFn4TrdPmF0aSvmHp6rPzodV8AwG9pOMYo")

# OpenRouter API keys — biri ishlamasa keyingisi ishlatiladi
OPENROUTER_API_KEYS = [
    os.getenv("OPENROUTER_API_KEY", "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"),
    os.getenv("OPENROUTER_API_KEY_2", "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"),
]
OPENROUTER_API_KEY = OPENROUTER_API_KEYS[0]  # muvofiqligi uchun

# Groq API keys — biri ishlamasa keyingisi ishlatiladi
GROQ_API_KEYS = [
    os.getenv("GROQ_API_KEY", "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"),
    os.getenv("GROQ_API_KEY_2", "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"),
]
GROQ_API_KEY = GROQ_API_KEYS[0]

OPENROUTER_MODEL = "google/gemma-3-27b-it:free"
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "40b04eb91a04e3e425ebd571e1b42687cece3007")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY", "654d460e38f64a468870bc954d63a87d")
MUXLISA_API_KEY = os.getenv("MUXLISA_API_KEY", "9Rpp-wBt00ouRnxYMVxZicBjRFdAwcOO8ADp2vZ5")
OCR_SPACE_API_KEY = os.getenv("OCR_SPACE_API_KEY", "K88044204688957")
NINJAS_API_KEY = os.getenv("NINJAS_API_KEY", "q1UAGdHWBqCx052A9rSvhuI3hfmqCDNCvPb3fTro")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bot.db")
