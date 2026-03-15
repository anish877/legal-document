from __future__ import annotations

from backend.services.text_normalizer import text_normalizer


class PreprocessingService:
    def clean_legal_text(self, text: str) -> str:
        return text_normalizer.clean_text(text)

    def recursive_character_splitter(
        self,
        text: str,
        max_chars: int = 8000,
        overlap: int = 500,
        separators: list[str] | None = None,
    ) -> list[str]:
        return text_normalizer.split_chunks(text, max_chars=max_chars, overlap=overlap)


preprocessing_service = PreprocessingService()
