from __future__ import annotations

from backend.services.analysis_pipeline import analysis_pipeline


class VerdictService:
    def detect_final_verdict(self, text: str) -> str:
        return analysis_pipeline.analyze(text).verdict


verdict_service = VerdictService()
