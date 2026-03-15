from __future__ import annotations

import re

from backend.services.analysis_config import AnalysisConfig, analysis_config
from backend.services.analysis_types import NormalizedDocument


class TextNormalizer:
    header_footer_pattern = re.compile(
        r"(?im)^(page\s+\d+(\s+of\s+\d+)?|confidential|draft|electronically signed|digitally signed)\s*$"
    )
    page_number_pattern = re.compile(r"(?im)^\s*\d+\s*$")
    whitespace_pattern = re.compile(r"[ \t]+")
    repeated_newlines_pattern = re.compile(r"\n{3,}")
    sentence_split_pattern = re.compile(r"(?<=[.!?])\s+")

    def __init__(self, config: AnalysisConfig | None = None) -> None:
        self.config = config or analysis_config

    def normalize_document(self, text: str) -> NormalizedDocument:
        cleaned_text = self.clean_text(text)
        truncated = self.truncate_text(cleaned_text, self.config.max_analysis_chars)
        sentences = tuple(self.split_sentences(truncated))
        chunks = tuple(self.split_chunks(truncated))
        return NormalizedDocument(text=truncated, sentences=sentences, chunks=chunks)

    def clean_text(self, text: str) -> str:
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
            cleaned_lines.append(self.whitespace_pattern.sub(" ", stripped))

        cleaned = "\n".join(cleaned_lines)
        cleaned = self.repeated_newlines_pattern.sub("\n\n", cleaned)
        return cleaned.strip()

    def truncate_text(self, text: str, max_chars: int | None = None) -> str:
        limit = max_chars or self.config.max_analysis_chars
        if len(text) <= limit:
            return text

        window = text[:limit]
        candidates = [window.rfind("\n\n"), window.rfind(". "), window.rfind("\n")]
        split_at = max(candidates)
        if split_at > int(limit * 0.7):
            return window[:split_at].strip()
        return window.strip()

    def split_sentences(self, text: str) -> list[str]:
        normalized = self.clean_text(text)
        if not normalized:
            return []
        sentences = [item.strip() for item in self.sentence_split_pattern.split(normalized) if item.strip()]
        if sentences:
            return sentences
        return [normalized]

    def split_chunks(self, text: str, max_chars: int | None = None, overlap: int | None = None) -> list[str]:
        normalized = self.clean_text(text)
        if not normalized:
            return []

        chunk_size = max_chars or self.config.max_chunk_chars
        chunk_overlap = overlap if overlap is not None else self.config.chunk_overlap_chars
        if len(normalized) <= chunk_size:
            return [normalized]

        chunks: list[str] = []
        start = 0
        length = len(normalized)

        while start < length:
            end = min(start + chunk_size, length)
            if end < length:
                split_at = max(
                    normalized.rfind("\n\n", start, end),
                    normalized.rfind(". ", start, end),
                    normalized.rfind("\n", start, end),
                )
                if split_at > start + int((end - start) * 0.6):
                    end = split_at + 1

            chunk = normalized[start:end].strip()
            if chunk:
                chunks.append(chunk)

            if end >= length:
                break
            start = max(0, end - chunk_overlap)

        return chunks


text_normalizer = TextNormalizer()
