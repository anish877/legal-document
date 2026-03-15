from __future__ import annotations

from backend.services.analysis_pipeline import analysis_pipeline


class ClauseService:
    def extract_clauses(self, text: str) -> dict:
        return analysis_pipeline.analyze(text).clauses


clause_service = ClauseService()
