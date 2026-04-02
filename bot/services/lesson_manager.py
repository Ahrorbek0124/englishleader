from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, List

@dataclass(frozen=True)
class GrammarLesson:
    topic: str
    uzbek_name: str
    explanation: str
    examples: List[str]

@dataclass(frozen=True)
class VideoLesson:
    topic: str
    uzbek_name: str
    url: str

class LessonManager:
    def __init__(self) -> None:
        self._grammar: Dict[str, GrammarLesson] = {}
        self._videos: Dict[str, VideoLesson] = {}
        self._init_data()
        
    def _init_data(self) -> None:
        # Recreated Grammar Data
        self._grammar["Nouns"] = GrammarLesson(
            topic="Nouns",
            uzbek_name="Otlar",
            explanation="Ingliz tilida otlar shaxs, narsa va joylarni bildiradi. Ular sanaladigan (countable) va sanalmaydigan (uncountable) bo'lishi mumkin.",
            examples=["Dog (It) - Dogs (Itlar)", "Water (Suv) - (sanalmaydi)"]
        )
        self._grammar["Articles"] = GrammarLesson(
            topic="Articles",
            uzbek_name="Artikllar",
            explanation="Ingliz tilida uchta artikl bor: a, an, the. 'A/An' noaniq predmetlar uchun, 'The' aniq predmetlar uchun ishlatiladi.",
            examples=["A book (qandaydir kitob)", "An apple (qandaydir olma)", "The sun (aniq quyosh)"]
        )
        self._grammar["Pronouns"] = GrammarLesson(
            topic="Pronouns",
            uzbek_name="Olmoshlar",
            explanation="Kishilik olmoshlari otning o'rniga ishlatiladi: I, you, he, she, it, we, they.",
            examples=["He is a doctor (U shifokor)", "They are students (Ular talabalar)"]
        )
        
        # Recreated Video Links (General placeholders for English learning)
        self._videos["Grammar Basics"] = VideoLesson(
            topic="Grammar Basics",
            uzbek_name="Boshlang'ich Grammatika",
            url="https://www.youtube.com/results?search_query=english+grammar+for+beginners+uzbek"
        )
        self._videos["Speaking Practice"] = VideoLesson(
            topic="Speaking Practice",
            uzbek_name="So'zlashuv Darslari",
            url="https://www.youtube.com/results?search_query=english+speaking+practice+uzbek"
        )
        self._videos["Vocabulary"] = VideoLesson(
            topic="Vocabulary",
            uzbek_name="Lug'at Boyligi",
            url="https://www.youtube.com/results?search_query=english+vocabulary+words+with+uzbek+meaning"
        )

    def get_grammar_topics(self) -> List[str]:
        return [f"{k} - {v.uzbek_name}" for k,v in self._grammar.items()]

    def get_grammar_info(self, topic: str) -> Optional[str]:
        lesson = self._grammar.get(topic)
        if not lesson:
            return None
        ex_str = "\n".join([f"• {ex}" for ex in lesson.examples])
        return f"📖 *{lesson.topic} ({lesson.uzbek_name})*\n\n{lesson.explanation}\n\nMisollar:\n{ex_str}"
        
    def get_video_topics(self) -> List[str]:
        return [f"{k} - {v.uzbek_name}" for k,v in self._videos.items()]
        
    def get_video_info(self, topic: str) -> Optional[str]:
        vid = self._videos.get(topic)
        if not vid:
            return None
        return f"🎥 *{vid.topic} ({vid.uzbek_name})*\n\nUshbu mavzudagi darslarni ko'rish uchun quyidagi havolaga o'ting:\n{vid.url}"
