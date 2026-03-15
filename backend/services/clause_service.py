from __future__ import annotations

from ai.clause_detector import legal_clause_detector


class ClauseService:
    def extract_clauses(self, text: str) -> dict:
        return legal_clause_detector.extract_clauses(text)


clause_service = ClauseService()
