import aiohttp
import logging
from typing import List, Dict, Optional
import html
import random
import json

from bot.ai.openrouter import ask_openrouter

logger = logging.getLogger(__name__)

class TestManager:
    def __init__(self):
        self.opentdb_url = "https://opentdb.com/api.php"

    async def get_opentdb_questions(self, amount: int = 5, difficulty: str = "medium") -> Optional[List[Dict]]:
        params = {
            "amount": amount,
            "difficulty": difficulty,
            "type": "multiple"
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.opentdb_url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("response_code") == 0:
                            results = data.get("results", [])
                            formatted_questions = []
                            for q in results:
                                options = q['incorrect_answers'] + [q['correct_answer']]
                                random.shuffle(options)
                                formatted_questions.append({
                                    "question": html.unescape(q['question']),
                                    "options": [html.unescape(opt) for opt in options],
                                    "correct_answer": html.unescape(q['correct_answer'])
                                })
                            return formatted_questions
        except Exception as e:
            logger.error(f"OpenTDB error: {e}")
        return None

    async def generate_ai_quiz(self, topic: str, difficulty: str = "medium", count: int = 5) -> Optional[List[Dict]]:
        """Generate quiz questions using OpenRouter AI."""
        prompt = f"""
        Create {count} {difficulty} difficulty multiple choice English grammar questions about {topic}.
        Return ONLY a JSON array, exactly like this:
        [
          {{
            "question": "She __ to the market yesterday.",
            "options": ["go", "went", "goes", "gone"],
            "correct": 1,
            "explanation": "Past Simple ishlatiladi. 'go' ning V2 shakli 'went'."
          }}
        ]
        NO OTHER TEXT. NO MARKDOWN TICKS. JUST JSON ARRAY.
        """
        res = await ask_openrouter("Generate quiz", system_prompt=prompt, temperature=0.8)
        if not res:
            return None
        try:
            if res.startswith("```json"):
                res = res[7:-3]
            elif res.startswith("```"):
                res = res[3:-3]
            questions = json.loads(res.strip())
            if isinstance(questions, list) and len(questions) > 0:
                return questions
        except Exception as e:
            logger.error(f"Failed to parse AI quiz response: {e}")
        return None

    async def get_questions(self, topic: str = "general", amount: int = 5, difficulty: str = "medium") -> List[Dict]:
        if topic == "general":
            questions = await self.get_opentdb_questions(amount=amount, difficulty=difficulty)
            if questions:
                return questions
        
        # Fallback to OpenRouter AI
        ai_questions = await self.generate_ai_quiz(topic, difficulty, amount)
        if ai_questions:
            return ai_questions

        # Final static fallback
        return [
            {
                "question": "Which sentence is correct?",
                "options": ["I is a student.", "I am a student.", "I are a student.", "I be a student."],
                "correct": 1,
                "explanation": "'I am' is the correct form of the verb 'to be' for first person singular."
            }
        ]

test_manager = TestManager()
