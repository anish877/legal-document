from __future__ import annotations

import math
import re
from collections import Counter

from backend.services.analysis_config import AnalysisConfig, analysis_config
from backend.services.analysis_types import NormalizedDocument, SummaryArtifacts


class SummaryEngine:
    word_pattern = re.compile(r"\b[a-zA-Z][a-zA-Z'-]{1,}\b")
    location_pattern = re.compile(
        r"(?i)\b(?:at|in|from|located at|executed at|court of)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,2})\b"
    )
    money_pattern = re.compile(r"(?:₹\s?\d[\d,]*(?:\.\d{1,2})?|Rs\.?\s?\d[\d,]*(?:\.\d{1,2})?|\$\s?\d[\d,]*(?:\.\d{1,2})?)")
    clause_keywords = {
        "Payment Clause": ("payment", "invoice", "fees", "consideration"),
        "Confidentiality Clause": ("confidentiality", "non-disclosure", "proprietary information"),
        "Termination Clause": ("termination", "material breach", "notice period"),
        "Governing Law Clause": ("governing law", "jurisdiction", "venue", "dispute resolution"),
    }
    document_type_keywords = (
        ("Non-Disclosure Agreement", ("non-disclosure", "confidentiality agreement", "nda")),
        ("Partnership Agreement", ("partnership", "partners", "partner a", "partner b")),
        ("Service Agreement", ("service agreement", "services agreement", "scope of work")),
        ("Employment Agreement", ("employment agreement", "employee", "employer")),
        ("Lease Agreement", ("lease", "lessor", "lessee", "rent")),
        ("Memorandum of Understanding", ("memorandum of understanding", "mou")),
        ("Court Order", ("court order", "ordered that", "petition", "respondent")),
        ("Judgment", ("judgment", "justice", "court", "appellant")),
        ("Legal Agreement", ("agreement", "party", "parties")),
    )
    stopwords = {
        "the",
        "and",
        "for",
        "that",
        "with",
        "this",
        "from",
        "into",
        "there",
        "their",
        "shall",
        "such",
        "have",
        "has",
        "been",
        "will",
        "were",
        "which",
        "under",
        "upon",
        "hereby",
        "whereas",
        "party",
        "parties",
        "agreement",
    }

    def __init__(self, config: AnalysisConfig | None = None) -> None:
        self.config = config or analysis_config

    def summarize(self, document: NormalizedDocument) -> SummaryArtifacts:
        if not document.text:
            return SummaryArtifacts(summary="", short_summary="", chunk_summaries=tuple())

        chunk_summaries = tuple(
            self._summarize_sentences(
                self._split_chunk_sentences(chunk),
                max_sentences=self.config.summary_chunk_sentence_limit,
            )
            for chunk in document.chunks
        )
        overview_source = " ".join(item for item in chunk_summaries if item) or document.text
        summary = self._summarize_sentences(
            [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", overview_source) if sentence.strip()],
            max_sentences=self.config.summary_sentence_limit,
        )

        if not summary:
            summary = document.text[:1200].strip()

        short_summary = self._short_summary(summary)

        if self.config.enable_abstractive_summary:
            abstractive_summary = self._abstractive_summary(document.text)
            if abstractive_summary:
                summary = abstractive_summary
                short_summary = self._short_summary(summary)

        return SummaryArtifacts(
            summary=summary,
            short_summary=short_summary,
            chunk_summaries=tuple(item for item in chunk_summaries if item),
        )

    def infer_document_type(self, text: str) -> str:
        lowered = text.casefold()
        for label, keywords in self.document_type_keywords:
            if any(keyword in lowered for keyword in keywords):
                return label
        return "Legal Document"

    def extract_locations(self, text: str) -> list[str]:
        return self._unique_values(self.location_pattern.findall(text))[:4]

    def extract_financial_terms(self, text: str) -> list[str]:
        return self._unique_values(self.money_pattern.findall(text))[:4]

    def extract_clause_highlights(self, text: str) -> list[str]:
        lowered = text.casefold()
        highlights: list[str] = []
        for label, keywords in self.clause_keywords.items():
            if any(keyword in lowered for keyword in keywords):
                highlights.append(label)
        return highlights[:6]

    def _split_chunk_sentences(self, chunk: str) -> list[str]:
        return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", chunk) if sentence.strip()]

    def _summarize_sentences(self, sentences: list[str], max_sentences: int) -> str:
        ranked = self._rank_sentences(sentences)
        if not ranked:
            return ""

        selected_indexes = sorted(index for index, _ in ranked[:max_sentences])
        chosen = [sentences[index] for index in selected_indexes]
        return " ".join(chosen).strip()

    def _rank_sentences(self, sentences: list[str]) -> list[tuple[int, float]]:
        filtered_sentences = [sentence for sentence in sentences if self._sentence_word_count(sentence) >= self.config.min_summary_sentence_words]
        if not filtered_sentences:
            filtered_sentences = sentences
        if not filtered_sentences:
            return []

        term_weights = self._term_weights(filtered_sentences)
        ranked: list[tuple[int, float]] = []

        for index, sentence in enumerate(sentences):
            word_count = self._sentence_word_count(sentence)
            if not sentence.strip() or word_count == 0:
                continue

            tokens = [token for token in self.word_pattern.findall(sentence.lower()) if token not in self.stopwords]
            lexical_score = sum(term_weights.get(token, 0.0) for token in tokens)
            position_bonus = max(0.0, 1.0 - (index / max(len(sentences), 1)))
            heading_bonus = 0.6 if len(sentence) < 120 and ":" in sentence[:60] else 0.0
            length_penalty = 0.15 if word_count > 45 else 0.0
            score = lexical_score + position_bonus + heading_bonus - length_penalty
            ranked.append((index, score))

        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked

    def _term_weights(self, sentences: list[str]) -> dict[str, float]:
        counts = Counter(
            token
            for sentence in sentences
            for token in self.word_pattern.findall(sentence.lower())
            if token not in self.stopwords
        )
        if not counts:
            return {}

        total = sum(counts.values())
        return {token: math.log1p(count) / total for token, count in counts.items()}

    def _short_summary(self, summary: str) -> str:
        sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", summary) if item.strip()]
        if len(sentences) <= 2:
            return summary.strip()
        return " ".join(sentences[:2]).strip()

    def _abstractive_summary(self, text: str) -> str:
        try:
            from ai.summarizer import legal_summarizer

            payload = legal_summarizer.summarize_document(text)
            return str(payload.get("summary", "")).strip()
        except Exception:
            return ""

    def _sentence_word_count(self, sentence: str) -> int:
        return len(self.word_pattern.findall(sentence))

    def _unique_values(self, values) -> list[str]:
        seen: set[str] = set()
        unique_values: list[str] = []

        for value in values:
            normalized = re.sub(r"\s+", " ", str(value)).strip(" .,;:")
            if not normalized:
                continue
            key = normalized.casefold()
            if key in seen:
                continue
            seen.add(key)
            unique_values.append(normalized)

        return unique_values


summary_engine = SummaryEngine()
