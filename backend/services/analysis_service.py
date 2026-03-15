from __future__ import annotations

import hashlib
from collections import OrderedDict
from threading import RLock

from fastapi import UploadFile

from backend.models.schemas import ClauseMap, DocumentAnalysisResponse, DocumentMetadata, EntityMap, InsightMap, RiskItem
from backend.services.clause_service import clause_service
from backend.services.document_service import document_service
from backend.services.entity_service import entity_service
from backend.services.preprocessing_service import preprocessing_service
from backend.services.risk_service import risk_service
from backend.services.summarization_service import summarization_service
from backend.services.verdict_service import verdict_service


class AnalysisService:
    def __init__(self, cache_size: int = 32) -> None:
        self.cache_size = cache_size
        self._analysis_cache: OrderedDict[str, dict] = OrderedDict()
        self._cache_lock = RLock()

    async def process_uploaded_file(self, file: UploadFile) -> DocumentAnalysisResponse:
        file_bytes = await file.read()
        parsed = await document_service.parse_upload(file.filename or "uploaded_document", file_bytes)

        cleaned_text = self._normalize_text(parsed["text"])
        analysis = self._analyze_document(cleaned_text)

        return DocumentAnalysisResponse(
            extracted_text=analysis["cleaned_text"],
            summary=analysis["summary"],
            detailed_summary=analysis["detailed_summary"],
            entities=EntityMap(**analysis["entities"]),
            insights=InsightMap(**analysis["insights"]),
            clauses=ClauseMap(**analysis["clauses"]),
            verdict=analysis["verdict"],
            risks=[RiskItem(**risk) for risk in analysis["risks"]],
            metadata=DocumentMetadata(
                filename=file.filename or "uploaded_document",
                file_type=parsed["file_type"],
                pages=parsed["pages"],
                scanned_pdf=parsed["scanned_pdf"],
                text_length=len(analysis["cleaned_text"]),
                chunk_count=analysis["chunk_count"],
            ),
            debug={"chunk_summaries": analysis["chunk_summaries"]},
        )

    def summarize_document(self, text: str) -> str:
        analysis = self._analyze_document(self._normalize_text(text))
        return analysis["summary"]

    def extract_entities(self, text: str) -> dict:
        analysis = self._analyze_document(self._normalize_text(text))
        return analysis["entities"]

    def extract_clauses(self, text: str) -> dict:
        analysis = self._analyze_document(self._normalize_text(text))
        return analysis["clauses"]

    def detect_final_verdict(self, text: str) -> str:
        analysis = self._analyze_document(self._normalize_text(text))
        return analysis["verdict"]

    def analyze_risks(self, text: str, clauses: dict | None = None, entities: dict | None = None, verdict: str | None = None) -> list[dict]:
        analysis = self._analyze_document(self._normalize_text(text))
        return analysis["risks"]

    def get_analysis(self, text: str) -> dict:
        return self._analyze_document(self._normalize_text(text))

    def _normalize_text(self, text: str) -> str:
        return preprocessing_service.clean_legal_text(text)

    def _analyze_document(self, cleaned_text: str) -> dict:
        cache_key = self._cache_key(cleaned_text)
        with self._cache_lock:
            cached = self._analysis_cache.get(cache_key)
            if cached is not None:
                self._analysis_cache.move_to_end(cache_key)
                return cached

        summary_payload = summarization_service.summarize_document(cleaned_text)
        chunks = preprocessing_service.recursive_character_splitter(cleaned_text)
        entities = entity_service.extract_entities(cleaned_text)
        clauses = clause_service.extract_clauses(cleaned_text)
        verdict = verdict_service.detect_final_verdict(cleaned_text)
        risks = risk_service.analyze_risks(cleaned_text, clauses, entities, verdict)
        insights = self._build_insights(summary_payload, entities, clauses, risks)

        analysis = {
            "cleaned_text": cleaned_text,
            "summary": summary_payload["summary"],
            "detailed_summary": summary_payload.get("detailed_summary", ""),
            "chunk_summaries": summary_payload["chunk_summaries"],
            "chunk_count": len(chunks),
            "entities": entities,
            "insights": insights,
            "clauses": clauses,
            "verdict": verdict,
            "risks": risks,
        }

        with self._cache_lock:
            self._analysis_cache[cache_key] = analysis
            self._analysis_cache.move_to_end(cache_key)
            if len(self._analysis_cache) > self.cache_size:
                self._analysis_cache.popitem(last=False)

        return analysis

    def _cache_key(self, cleaned_text: str) -> str:
        return hashlib.sha256(cleaned_text.encode("utf-8")).hexdigest()

    def _build_insights(self, summary_payload: dict, entities: dict, clauses: dict, risks: list[dict]) -> dict:
        summary_insights = summary_payload.get("insights", {})
        entity_parties = [
            party.get("name", "").strip()
            for party in entities.get("parties", [])
            if isinstance(party, dict) and party.get("name")
        ]
        entity_locations = [item for item in entities.get("locations", []) if item]
        entity_money = [item for item in (entities.get("money") or entities.get("monetary_values") or []) if item]

        important_clauses = [
            label
            for label, detail in (
                ("Payment Clause", clauses.get("payment_clause", {})),
                ("Confidentiality Clause", clauses.get("confidentiality_clause", {})),
                ("Termination Clause", clauses.get("termination_clause", {})),
                ("Governing Law Clause", clauses.get("governing_law_clause", {})),
            )
            if detail.get("present")
        ]
        important_clauses.extend(summary_insights.get("important_clauses", []))

        risk_flags = [risk.get("title", "").strip() for risk in risks if risk.get("title")]
        risk_flags.extend(summary_insights.get("risk_flags", []))

        return {
            "document_type": summary_insights.get("document_type", ""),
            "parties_inferred": self._unique_strings(entity_parties or summary_insights.get("parties_inferred", []))[:4],
            "locations": self._unique_strings(entity_locations or summary_insights.get("locations", []))[:4],
            "financial_terms": self._unique_strings(entity_money or summary_insights.get("financial_terms", []))[:4],
            "important_clauses": self._unique_strings(important_clauses)[:6],
            "risk_flags": self._unique_strings(risk_flags)[:6],
        }

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


analysis_service = AnalysisService()
