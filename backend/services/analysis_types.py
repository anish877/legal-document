from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NormalizedDocument:
    text: str
    sentences: tuple[str, ...]
    chunks: tuple[str, ...]


@dataclass(frozen=True)
class SummaryArtifacts:
    summary: str
    short_summary: str
    chunk_summaries: tuple[str, ...]


@dataclass(frozen=True)
class StageMetrics:
    durations: dict[str, float] = field(default_factory=dict)
    counters: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "durations": {name: round(value, 4) for name, value in self.durations.items()},
            "counters": self.counters,
        }


@dataclass(frozen=True)
class AnalysisContext:
    extracted_text: str
    normalized: NormalizedDocument
    metadata: dict[str, Any]
    page_details: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class AnalysisResult:
    cleaned_text: str
    summary: str
    detailed_summary: str
    chunk_summaries: tuple[str, ...]
    chunk_count: int
    entities: dict[str, Any]
    insights: dict[str, Any]
    clauses: dict[str, Any]
    verdict: str
    risks: list[dict[str, Any]]
    metrics: StageMetrics
