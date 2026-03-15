from __future__ import annotations

from backend.services.analysis_pipeline import analysis_pipeline


class EntityService:
    def extract_entities(self, text: str) -> dict:
        return analysis_pipeline.analyze(text).entities


entity_service = EntityService()
