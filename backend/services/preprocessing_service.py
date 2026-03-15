from __future__ import annotations

import re


class PreprocessingService:
    header_footer_pattern = re.compile(
        r"(?im)^(page\s+\d+(\s+of\s+\d+)?|confidential|draft|electronically signed|digitally signed)\s*$"
    )
    page_number_pattern = re.compile(r"(?im)^\s*\d+\s*$")
    whitespace_pattern = re.compile(r"[ \t]+")
    newline_pattern = re.compile(r"\n{3,}")

    def clean_legal_text(self, text: str) -> str:
        lines = text.splitlines()
        cleaned_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                cleaned_lines.append("")
                continue
            if self.header_footer_pattern.match(stripped):
                continue
            if self.page_number_pattern.match(stripped):
                continue
            normalized = self.whitespace_pattern.sub(" ", stripped)
            cleaned_lines.append(normalized)

        cleaned = "\n".join(cleaned_lines)
        cleaned = self.newline_pattern.sub("\n\n", cleaned)
        return cleaned.strip()

    def recursive_character_splitter(
        self,
        text: str,
        max_chars: int = 8000,
        overlap: int = 500,
        separators: list[str] | None = None,
    ) -> list[str]:
        separators = separators or ["\n\n", "\n", ". ", "; ", " "]
        text = text.strip()
        if len(text) <= max_chars:
            return [text] if text else []

        chunks: list[str] = []
        start = 0
        length = len(text)

        while start < length:
            end = min(start + max_chars, length)
            if end < length:
                split_end = self._find_best_split(text, start, end, separators)
                end = split_end if split_end > start else end

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            if end >= length:
                break
            start = max(0, end - overlap)

        return chunks

    def _find_best_split(self, text: str, start: int, end: int, separators: list[str]) -> int:
        window = text[start:end]
        for separator in separators:
            idx = window.rfind(separator)
            if idx > int(len(window) * 0.6):
                return start + idx + len(separator)
        return end


preprocessing_service = PreprocessingService()
