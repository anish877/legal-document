from __future__ import annotations

from ai.clause_detector import legal_clause_detector


class VerdictService:
    def detect_final_verdict(self, text: str) -> str:
        return legal_clause_detector.detect_final_verdict(text)


verdict_service = VerdictService()
