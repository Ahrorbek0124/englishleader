from __future__ import annotations

from typing import Dict, List, Optional
from pathlib import Path

import requests


class DictionaryManager:
    DICTIONARY_FILE = "80-000-dictionary.pdf"
    WORDS_PER_SECTION = 1000
    WORDS_PER_SUBSECTION = 100

    def __init__(self) -> None:
        self.en_to_uz_dictionary: Dict[str, List[str]] = {}
        self.uz_to_en_dictionary: Dict[str, List[str]] = {}
        self.sections: List[List[str]] = []

        # HTTP-based translators backed by Tahrirchi API.
        self._api_key: Optional[str] = self._load_api_key()

        self.load_dictionary()

    @staticmethod
    def _load_api_key() -> Optional[str]:
        """
        Load Tahrirchi API key from local file next to this module.
        The file must contain only the API key string (th_...).
        """
        token_file = Path(__file__).with_name("tahrirchi_api_key.txt")
        if not token_file.exists():
            return None
        content = token_file.read_text(encoding="utf-8").strip()
        return content or None

    def load_dictionary(self) -> None:
        """
        Initialize dictionaries and, if available, online translators.

        The original Java version used a large PDF dictionary (80,000+ words).
        That file is not present in this Python project yet, so for now we keep
        the in‑memory dictionaries empty and rely on an online translator.
        When you add real dictionary files later, extend this method to load
        them into self.en_to_uz_dictionary / self.uz_to_en_dictionary.
        """
        # Do NOT prefill with hard‑coded words – you said you will upload
        # your own dictionaries later. For now sections stay empty.
        self.sections = []

    def add_dictionary_entry(self, english: str, uzbek_list: List[str]) -> None:
        key = english.lower()
        self.en_to_uz_dictionary[key] = uzbek_list

        for uz in uzbek_list:
            uz_key = uz.lower()
            if uz_key not in self.uz_to_en_dictionary:
                self.uz_to_en_dictionary[uz_key] = []
            self.uz_to_en_dictionary[uz_key].append(english)

    def get_en_to_uz_translation(self, word: str) -> str:
        # 1) Try local dictionary (useful when you add your own data files).
        translations = self.en_to_uz_dictionary.get(word.lower())
        if translations:
            return ", ".join(translations)

        # 2) Fall back to Tahrirchi API if key is available.
        if self._api_key:
            try:
                return self._translate_via_tahrirchi(word, source_lang="en", target_lang="uz")
            except Exception:
                return "Tarjima vaqtida xatolik yuz berdi"

        return "So'z topilmadi"

    def get_uz_to_en_translation(self, word: str) -> str:
        # 1) Try local dictionary.
        translations = self.uz_to_en_dictionary.get(word.lower())
        if translations:
            return ", ".join(translations)

        # 2) Fall back to Tahrirchi API if key is available.
        if self._api_key:
            try:
                text = self._translate_via_tahrirchi(word, source_lang="uz", target_lang="en")
                return text or "Translation not found"
            except Exception:
                return "Error while translating"

        return "Word not found"

    def _translate_via_tahrirchi(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Call Tahrirchi translate-v2 HTTP API.

        NOTE: The exact request/response schema is assumed based on typical
        translation APIs and may need adjustment if the API changes.
        """
        if not self._api_key:
            raise RuntimeError("Tahrirchi API key is missing")

        url = "https://websocket.tahrirchi.uz/translate-v2"
        headers = {
            "Authorization": f"Token {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "source_lang": source_lang,
            "target_lang": target_lang,
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # Expected shape: {"translation": "..."} or {"result": "..."}.
        if isinstance(data, dict):
            if "translation" in data:
                return str(data["translation"])
            if "result" in data:
                return str(data["result"])
        return str(data)

    def get_section(self, section_number: int) -> List[str]:
        if section_number < 1 or section_number > len(self.sections):
            return []
        return self.sections[section_number - 1]

    def get_subsection(self, section_number: int, subsection_number: int) -> List[str]:
        section = self.get_section(section_number)
        if not section:
            return []

        start_index = (subsection_number - 1) * self.WORDS_PER_SUBSECTION
        end_index = min(start_index + self.WORDS_PER_SUBSECTION, len(section))

        if start_index >= len(section):
            return []

        return section[start_index:end_index]

    def get_total_sections(self) -> int:
        return len(self.sections)

    def get_subsections_in_section(self, section_number: int) -> int:
        section = self.get_section(section_number)
        if not section:
            return 0
        # Ceiling division
        return (len(section) + self.WORDS_PER_SUBSECTION - 1) // self.WORDS_PER_SUBSECTION

