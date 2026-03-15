from __future__ import annotations

import hashlib
import logging
from collections import OrderedDict
from threading import RLock
from time import perf_counter

from backend.services.analysis_config import AnalysisConfig, analysis_config
from backend.services.analysis_types import AnalysisContext, AnalysisResult, StageMetrics
from backend.services.clause_engine import ClauseEngine, clause_engine
from backend.services.entity_engine import EntityEngine, entity_engine
from backend.services.risk_service import risk_service
from backend.services.summary_engine import SummaryEngine, summary_engine
from backend.services.text_normalizer import TextNormalizer, text_normalizer
from backend.services.verdict_engine import VerdictEngine, verdict_engine


logger = logging.getLogger(__name__)


class AnalysisPipeline:
    def __init__(
        self,
        config: AnalysisConfig | None = None,
        normalizer: TextNormalizer | None = None,
        summary: SummaryEngine | None = None,
        entities: EntityEngine | None = None,
        clauses: ClauseEngine | None = None,
        verdicts: VerdictEngine | None = None,
        cache_size: int = 32,
    ) -> None:
        self.config = config or analysis_config
        self.normalizer = normalizer or text_normalizer
        self.summary_engine = summary or summary_engine
        self.entity_engine = entities or entity_engine
        self.clause_engine = clauses or clause_engine
        self.verdict_engine = verdicts or verdict_engine
        self.cache_size = cache_size
        self._analysis_cache: OrderedDict[str, AnalysisResult] = OrderedDict()
        self._cache_lock = RLock()

    def analyze(
        self,
        text: str,
        metadata: dict | None = None,
        page_details: list[dict] | None = None,
        progress_callback=None,
    ) -> AnalysisResult:
        normalize_start = perf_counter()
        normalized = self.normalizer.normalize_document(text)
        normalize_seconds = perf_counter() - normalize_start
        cache_key = self._cache_key(normalized.text)

        with self._cache_lock:
            cached = self._analysis_cache.get(cache_key)
            if cached is not None:
                self._analysis_cache.move_to_end(cache_key)
                self._emit_progress(
                    progress_callback,
                    stage="analyze",
                    message="Reused cached analysis.",
                    progress=0.9,
                )
                return cached

        context = AnalysisContext(
            extracted_text=text,
            normalized=normalized,
            metadata=metadata or {},
            page_details=tuple(page_details or ()),
        )
        self._emit_progress(
            progress_callback,
            stage="normalize",
            message="Normalized and segmented document text.",
            progress=0.42,
            detail={
                "sentence_count": len(normalized.sentences),
                "chunk_count": len(normalized.chunks),
            },
        )
        result = self._compute_analysis(context, normalize_seconds, progress_callback)

        with self._cache_lock:
            self._analysis_cache[cache_key] = result
            self._analysis_cache.move_to_end(cache_key)
            if len(self._analysis_cache) > self.cache_size:
                self._analysis_cache.popitem(last=False)

        return result

    def _compute_analysis(self, context: AnalysisContext, normalize_seconds: float, progress_callback=None) -> AnalysisResult:
        durations: dict[str, float] = {"normalize": normalize_seconds}
        cleaned_text = context.normalized.text

        self._emit_progress(progress_callback, stage="summarize", message="Building concise summary.", progress=0.55)
        start = perf_counter()
        summary_payload = self.summary_engine.summarize(context.normalized)
        durations["summarize"] = perf_counter() - start

        self._emit_progress(progress_callback, stage="entities", message="Extracting entities and parties.", progress=0.67)
        start = perf_counter()
        entities = self.entity_engine.extract(cleaned_text)
        durations["entities"] = perf_counter() - start

        self._emit_progress(progress_callback, stage="clauses", message="Detecting clauses and key obligations.", progress=0.77)
        start = perf_counter()
        clauses = self.clause_engine.extract(cleaned_text)
        durations["clauses"] = perf_counter() - start

        self._emit_progress(progress_callback, stage="verdict", message="Checking for document outcome.", progress=0.84)
        start = perf_counter()
        verdict = self.verdict_engine.detect(cleaned_text)
        durations["verdict"] = perf_counter() - start

        self._emit_progress(progress_callback, stage="risks", message="Scoring legal risk signals.", progress=0.9)
        start = perf_counter()
        risks = risk_service.analyze_risks(cleaned_text, clauses, entities, verdict)
        durations["risks"] = perf_counter() - start

        insights = self._build_insights(cleaned_text, entities, clauses, risks)
        detailed_summary = self._build_detailed_summary(summary_payload.summary, insights, verdict, risks)

        metrics = StageMetrics(
            durations=durations,
            counters={
                "text_length": len(cleaned_text),
                "sentence_count": len(context.normalized.sentences),
                "chunk_count": len(context.normalized.chunks),
            },
        )
        logger.info("analysis_metrics=%s", metrics.as_dict())
        self._emit_progress(
            progress_callback,
            stage="complete",
            message="Analysis artifacts are ready.",
            progress=0.97,
            detail=metrics.as_dict(),
        )

        return AnalysisResult(
            cleaned_text=cleaned_text,
            summary=summary_payload.short_summary or summary_payload.summary,
            detailed_summary=detailed_summary,
            chunk_summaries=summary_payload.chunk_summaries,
            chunk_count=len(context.normalized.chunks),
            entities=entities,
            insights=insights,
            clauses=clauses,
            verdict=verdict,
            risks=risks,
            metrics=metrics,
        )

    def _build_insights(self, text: str, entities: dict, clauses: dict, risks: list[dict]) -> dict:
        party_names = [
            party.get("name", "").strip()
            for party in entities.get("parties", [])
            if isinstance(party, dict) and party.get("name")
        ]
        locations = list(entities.get("locations", [])) or self.summary_engine.extract_locations(text)
        financial_terms = list(entities.get("money") or entities.get("monetary_values") or []) or self.summary_engine.extract_financial_terms(text)

        important_clauses = [
            detail.get("clause", clause_name.replace("_", " ").title())
            for clause_name, detail in clauses.items()
            if detail.get("present")
        ]
        if not important_clauses:
            important_clauses = self.summary_engine.extract_clause_highlights(text)

        risk_flags = [risk.get("title", "").strip() for risk in risks if risk.get("title")]

        return {
            "document_type": self.summary_engine.infer_document_type(text),
            "parties_inferred": self._unique_strings(party_names)[:4],
            "locations": self._unique_strings(locations)[:4],
            "financial_terms": self._unique_strings(financial_terms)[:4],
            "important_clauses": self._unique_strings(important_clauses)[:6],
            "risk_flags": self._unique_strings(risk_flags)[:6],
        }

    def _build_detailed_summary(self, summary: str, insights: dict, verdict: str, risks: list[dict]) -> str:
        key_parties = ", ".join(insights.get("parties_inferred", [])) or "No clear parties were inferred from the available text."

        terms: list[str] = []
        if insights.get("document_type"):
            terms.append(f"Document Type: {insights['document_type']}")
        if insights.get("locations"):
            terms.append(f"Locations: {', '.join(insights['locations'])}")
        if insights.get("financial_terms"):
            terms.append(f"Financial Terms: {', '.join(insights['financial_terms'])}")
        important_terms = " ".join(terms) or "No material terms were clearly extracted."

        main_clauses = ", ".join(insights.get("important_clauses", [])) or "No major clause themes were confidently identified."

        conclusion_parts: list[str] = []
        if verdict and verdict != "Verdict not clearly detected":
            conclusion_parts.append(f"Verdict: {verdict}.")
        if risks:
            conclusion_parts.append(f"Top Risk: {risks[0]['title']} - {risks[0]['description']}")
        if not conclusion_parts:
            conclusion_parts.append("Review the full document for precise legal interpretation.")

        sections = [
            ("Document Overview", summary or "No summary could be generated."),
            ("Key Parties", key_parties),
            ("Important Terms", important_terms),
            ("Main Clauses", main_clauses),
            ("Conclusion", " ".join(conclusion_parts).strip()),
        ]
        return "\n\n".join(f"{title}: {content}".strip() for title, content in sections if content).strip()

    def _cache_key(self, cleaned_text: str) -> str:
        return hashlib.sha256(cleaned_text.encode("utf-8")).hexdigest()

    def _unique_strings(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        unique_values: list[str] = []

        for value in values:
            normalized = " ".join(str(value).split()).strip(" .,;:")
            if not normalized:
                continue
            key = normalized.casefold()
            if key in seen:
                continue
            seen.add(key)
            unique_values.append(normalized)

        return unique_values

    def _emit_progress(self, callback, stage: str, message: str, progress: float, detail: dict | None = None) -> None:
        if callback is None:
            return
        callback(
            {
                "stage": stage,
                "message": message,
                "progress": round(progress, 3),
                "detail": detail or {},
            }
        )


analysis_pipeline = AnalysisPipeline()
