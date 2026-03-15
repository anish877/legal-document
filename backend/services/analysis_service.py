from __future__ import annotations

from time import perf_counter

from fastapi import UploadFile

from backend.models.schemas import ClauseMap, DocumentAnalysisResponse, DocumentMetadata, EntityMap, InsightMap, RiskItem
from backend.services.analysis_pipeline import analysis_pipeline
from backend.services.document_service import document_service


class AnalysisService:
    async def process_uploaded_file(self, file: UploadFile) -> DocumentAnalysisResponse:
        file_bytes = await file.read()
        return await self.process_uploaded_bytes(file.filename or "uploaded_document", file_bytes)

    async def process_uploaded_bytes(self, filename: str, file_bytes: bytes, progress_callback=None) -> DocumentAnalysisResponse:
        parse_start = perf_counter()
        if progress_callback is not None:
            progress_callback(
                {
                    "stage": "upload",
                    "message": "File received by backend.",
                    "progress": 0.06,
                    "detail": {"filename": filename, "size_bytes": len(file_bytes)},
                }
            )
        parsed = await document_service.parse_upload(filename, file_bytes, progress_callback=progress_callback)
        parse_seconds = perf_counter() - parse_start
        analysis = analysis_pipeline.analyze(
            parsed["text"],
            metadata=parsed,
            page_details=parsed.get("page_details"),
            progress_callback=progress_callback,
        )
        metrics = analysis.metrics.as_dict()
        metrics["durations"]["parse"] = round(parse_seconds, 4)
        metrics["durations"]["ocr"] = float(parsed.get("ocr_seconds", 0.0))
        metrics["counters"]["page_count"] = parsed.get("pages")
        metrics["counters"]["page_modes"] = parsed.get("page_details", [])

        return DocumentAnalysisResponse(
            extracted_text=analysis.cleaned_text,
            summary=analysis.summary,
            detailed_summary=analysis.detailed_summary,
            entities=EntityMap(**analysis.entities),
            insights=InsightMap(**analysis.insights),
            clauses=ClauseMap(**analysis.clauses),
            verdict=analysis.verdict,
            risks=[RiskItem(**risk) for risk in analysis.risks],
            metadata=DocumentMetadata(
                filename=filename or "uploaded_document",
                file_type=parsed["file_type"],
                pages=parsed["pages"],
                scanned_pdf=parsed["scanned_pdf"],
                text_length=len(analysis.cleaned_text),
                chunk_count=analysis.chunk_count,
            ),
            debug={
                "chunk_summaries": list(analysis.chunk_summaries),
                "metrics": metrics,
                "page_modes": parsed.get("page_details", []),
            },
        )

    def summarize_document(self, text: str) -> str:
        analysis = self.get_analysis(text)
        return analysis["summary"]

    def extract_entities(self, text: str) -> dict:
        analysis = self.get_analysis(text)
        return analysis["entities"]

    def extract_clauses(self, text: str) -> dict:
        analysis = self.get_analysis(text)
        return analysis["clauses"]

    def detect_final_verdict(self, text: str) -> str:
        analysis = self.get_analysis(text)
        return analysis["verdict"]

    def analyze_risks(self, text: str, clauses: dict | None = None, entities: dict | None = None, verdict: str | None = None) -> list[dict]:
        analysis = self.get_analysis(text)
        return analysis["risks"]

    def get_analysis(self, text: str) -> dict:
        analysis = analysis_pipeline.analyze(text)
        return {
            "cleaned_text": analysis.cleaned_text,
            "summary": analysis.summary,
            "detailed_summary": analysis.detailed_summary,
            "chunk_summaries": list(analysis.chunk_summaries),
            "chunk_count": analysis.chunk_count,
            "entities": analysis.entities,
            "insights": analysis.insights,
            "clauses": analysis.clauses,
            "verdict": analysis.verdict,
            "risks": analysis.risks,
            "metrics": analysis.metrics.as_dict(),
        }


analysis_service = AnalysisService()
