from __future__ import annotations

from backend.services.analysis_pipeline import analysis_pipeline


class SummarizationService:
    def summarize_document(self, text: str) -> dict:
        analysis = analysis_pipeline.analyze(text)
        return {
            "summary": analysis.summary,
            "detailed_summary": analysis.detailed_summary,
            "chunk_summaries": list(analysis.chunk_summaries),
            "chunk_count": analysis.chunk_count,
            "insights": analysis.insights,
        }


summarization_service = SummarizationService()
