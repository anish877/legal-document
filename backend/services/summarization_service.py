from __future__ import annotations

from ai.summarizer import legal_summarizer


class SummarizationService:
    def summarize_document(self, text: str) -> dict:
        return legal_summarizer.summarize_document(text)


summarization_service = SummarizationService()
