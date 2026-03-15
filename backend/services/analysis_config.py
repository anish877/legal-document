from __future__ import annotations

import os
from dataclasses import dataclass


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AnalysisConfig:
    max_analysis_chars: int = int(os.getenv("MAX_ANALYSIS_CHARS", "30000"))
    max_chunk_chars: int = int(os.getenv("MAX_CHUNK_CHARS", "5000"))
    chunk_overlap_chars: int = int(os.getenv("CHUNK_OVERLAP_CHARS", "250"))
    summary_sentence_limit: int = int(os.getenv("SUMMARY_SENTENCE_LIMIT", "6"))
    summary_chunk_sentence_limit: int = int(os.getenv("SUMMARY_CHUNK_SENTENCE_LIMIT", "3"))
    min_summary_sentence_words: int = int(os.getenv("MIN_SUMMARY_SENTENCE_WORDS", "6"))
    low_text_threshold: int = int(os.getenv("LOW_TEXT_THRESHOLD", "80"))
    scanned_ratio_threshold: float = float(os.getenv("SCANNED_RATIO_THRESHOLD", "0.5"))
    ocr_zoom: float = float(os.getenv("OCR_ZOOM", "2.0"))
    enable_abstractive_summary: bool = _env_flag("ENABLE_ABSTRACTIVE_SUMMARY", default=False)


analysis_config = AnalysisConfig()
