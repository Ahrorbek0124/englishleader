from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class TenseInfo:
    name: str
    uzbek_name: str
    structure: str
    examples: str
    video_link: str
    usage: str

    def __str__(self) -> str:
        return (
            f"{self.name} ({self.uzbek_name})\n\n"
            f"Struktura: {self.structure}\n\n"
            f"Misollar: {self.examples}\n\n"
            f"Qo'llanilishi:\n{self.usage}"
        )


class TenseManager:
    def __init__(self) -> None:
        self._tenses: Dict[str, TenseInfo] = {}
        self._initialize_tenses()

    def _initialize_tenses(self) -> None:
        # Present Simple
        present_simple = TenseInfo(
            name="Present Simple",
            uzbek_name="Hozirgi oddiy zamon",
            structure="Subject + V1/V1+s/es\nMasalan: I work. / He works.",
            examples="I work every day.\nHe works at a bank.",
            video_link="https://www.youtube.com/results?search_query=present+simple+tense+uzbek",
            usage=(
                "1. Doimiy odatlar va takrorlanuvchi ishlar: I go to school every day.\n"
                "2. Umumiy haqiqatlar va ilmiy faktlar: Water boils at 100°C.\n"
                "3. Jadval, reja bo'yicha harakatlar: The train leaves at 7 o'clock."
            ),
        )
        self._tenses["Present Simple"] = present_simple

        # Present Continuous
        present_continuous = TenseInfo(
            name="Present Continuous",
            uzbek_name="Hozirgi davomli zamon",
            structure="Subject + am/is/are + V-ing\nMasalan: I am working.",
            examples="I am studying now.\nThey are playing football.",
            video_link="https://www.youtube.com/results?search_query=present+continuous+tense+uzbek",
            usage=(
                "1. Hozirgi paytda davom etayotgan ishlar: She is reading now.\n"
                "2. Yaqin kelajakdagi rejalar: We are meeting tomorrow.\n"
                "3. Vaqtinchalik holatlar: I am living in Tashkent these days."
            ),
        )
        self._tenses["Present Continuous"] = present_continuous

        # Present Perfect
        present_perfect = TenseInfo(
            name="Present Perfect",
            uzbek_name="Hozirgi tugallangan zamon",
            structure="Subject + have/has + V3\nMasalan: I have finished my work.",
            examples="I have seen that movie.\nShe has visited London twice.",
            video_link="https://www.youtube.com/results?search_query=present+perfect+tense+uzbek",
            usage=(
                "1. Natijasi hozir seziladigan ishlar: I have lost my keys.\n"
                "2. Hayotiy tajriba: I have been to Samarkand.\n"
                "3. Hozirgacha davom etgan holatlar: She has lived here for 5 years."
            ),
        )
        self._tenses["Present Perfect"] = present_perfect

        # Present Perfect Continuous
        present_perfect_continuous = TenseInfo(
            name="Present Perfect Continuous",
            uzbek_name="Hozirgi tugallangan davomli zamon",
            structure="Subject + have/has been + V-ing\nMasalan: I have been studying.",
            examples="I have been working all day.\nThey have been waiting for an hour.",
            video_link="https://www.youtube.com/results?search_query=present+perfect+continuous+tense+uzbek",
            usage=(
                "1. O'tgan zamondan hozirgacha davom etayotgan ishlar: I have been reading for two hours.\n"
                "2. Uzoq vaqt davom etgan jarayonlar: She has been teaching since 2010."
            ),
        )
        self._tenses["Present Perfect Continuous"] = present_perfect_continuous

        # Past Simple
        past_simple = TenseInfo(
            name="Past Simple",
            uzbek_name="O'tgan oddiy zamon",
            structure="Subject + V2\nMasalan: I worked.",
            examples="I visited my grandparents yesterday.\nShe studied English last year.",
            video_link="https://www.youtube.com/results?search_query=past+simple+tense+uzbek",
            usage=(
                "1. O'tmishda aniq vaqtda tugallangan ishlar: I watched a film yesterday.\n"
                "2. Ketma-ket hodisalar: He came home, had dinner and went to bed."
            ),
        )
        self._tenses["Past Simple"] = past_simple

        # Past Continuous
        past_continuous = TenseInfo(
            name="Past Continuous",
            uzbek_name="O'tgan davomli zamon",
            structure="Subject + was/were + V-ing\nMasalan: I was working.",
            examples="I was reading when he called.\nThey were playing football at 5 o'clock.",
            video_link="https://www.youtube.com/results?search_query=past+continuous+tense+uzbek",
            usage=(
                "1. O'tmishda ma'lum bir vaqtda davom etayotgan ishlar.\n"
                "2. Ikki parallel davomli harakatlar: She was cooking while I was cleaning."
            ),
        )
        self._tenses["Past Continuous"] = past_continuous

        # Past Perfect
        past_perfect = TenseInfo(
            name="Past Perfect",
            uzbek_name="O'tgan tugallangan zamon",
            structure="Subject + had + V3\nMasalan: I had finished my work.",
            examples="I had left before he arrived.\nShe had already eaten by 8 o'clock.",
            video_link="https://www.youtube.com/results?search_query=past+perfect+tense+uzbek",
            usage=(
                "1. O'tgan zamondagi boshqa bir ish yoki vaqtdan oldin tugallangan ishlar.\n"
                "2. Sabab-natija ketma-ketligi: The ground was wet because it had rained."
            ),
        )
        self._tenses["Past Perfect"] = past_perfect

        # Past Perfect Continuous
        past_perfect_continuous = TenseInfo(
            name="Past Perfect Continuous",
            uzbek_name="O'tgan tugallangan davomli zamon",
            structure="Subject + had been + V-ing\nMasalan: I had been working.",
            examples="I had been studying for two hours before he arrived.\nThey had been playing when it started to rain.",
            video_link="https://www.youtube.com/results?search_query=past+perfect+continuous+tense+uzbek",
            usage=(
                "1. O'tgan zamonning ma'lum bir vaqtigacha davom etgan ishlar.\n"
                "2. Uzoq davom etgan jarayonning tugallanganligi: She was tired because she had been working all day."
            ),
        )
        self._tenses["Past Perfect Continuous"] = past_perfect_continuous

        # Future Simple
        future_simple = TenseInfo(
            name="Future Simple",
            uzbek_name="Kelajak oddiy zamon",
            structure="Subject + will/shall + V1\nMasalan: I will work.",
            examples="I will call you tomorrow.\nShe will start a new job next week.",
            video_link="https://www.youtube.com/results?search_query=future+simple+tense+uzbek",
            usage=(
                "1. Kelajakdagi reja va qarorlar: I will visit you next week.\n"
                "2. Vaqtinchalik qarorlar hozir qabul qilingan: I am thirsty, I will drink some water.\n"
                "3. Taxmin va bashoratlar: It will rain tomorrow."
            ),
        )
        self._tenses["Future Simple"] = future_simple

        # Future Continuous
        future_continuous = TenseInfo(
            name="Future Continuous",
            uzbek_name="Kelajak davomli zamon",
            structure="Subject + will be + V-ing\nMasalan: I will be working.",
            examples="I will be studying at 8 o'clock.\nThey will be travelling next month.",
            video_link="https://www.youtube.com/results?search_query=future+continuous+tense+uzbek",
            usage=(
                "1. Kelajakdagi ma'lum bir vaqtda davom etadigan ishlar.\n"
                "2. Uzoq davom etadigan jarayonlar: I will be working on this project for the next few weeks."
            ),
        )
        self._tenses["Future Continuous"] = future_continuous

        # Future Perfect
        future_perfect = TenseInfo(
            name="Future Perfect",
            uzbek_name="Kelajak tugallangan zamon",
            structure="Subject + will have + V3\nMasalan: I will have finished.",
            examples="I will have finished the report by Friday.\nShe will have left by 6 o'clock.",
            video_link="https://www.youtube.com/results?search_query=future+perfect+tense+uzbek",
            usage=(
                "1. Kelajakdagi biror muddatgacha tugallanishi kutilayotgan ishlar.\n"
                "2. Natija va yakun: By next year, I will have completed my studies."
            ),
        )
        self._tenses["Future Perfect"] = future_perfect

        # Future Perfect Continuous
        future_perfect_continuous = TenseInfo(
            name="Future Perfect Continuous",
            uzbek_name="Kelajak tugallangan davomli zamon",
            structure="Subject + will have been + V-ing\nMasalan: I will have been working.",
            examples="I will have been working here for ten years by next month.\nThey will have been travelling for hours.",
            video_link="https://www.youtube.com/results?search_query=future+perfect+continuous+tense+uzbek",
            usage=(
                "1. Kelajakdagi ma'lum bir vaqtgacha davom etib keladigan ishlar.\n"
                "2. Uzoq davom etishi kutilayotgan jarayonlar: By noon, she will have been studying for five hours."
            ),
        )
        self._tenses["Future Perfect Continuous"] = future_perfect_continuous

    def get_tense_info(self, tense: str) -> Optional[TenseInfo]:
        return self._tenses.get(tense)

