from __future__ import annotations

import logging

import spacy


logger = logging.getLogger(__name__)


class SpacyService:
    def __init__(self) -> None:
        self._nlp = None

    def get_model(self):
        if self._nlp is None:
            try:
                self._nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy model en_core_web_sm is not installed. Falling back to blank English pipeline.")
                self._nlp = spacy.blank("en")
            if "sentencizer" not in self._nlp.pipe_names:
                self._nlp.add_pipe("sentencizer")
        return self._nlp


spacy_service = SpacyService()
