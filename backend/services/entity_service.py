from __future__ import annotations

from ai.entity_extractor import legal_entity_extractor


class EntityService:
    def extract_entities(self, text: str) -> dict:
        return legal_entity_extractor.extract_entities(text)


entity_service = EntityService()
