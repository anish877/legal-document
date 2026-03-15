from __future__ import annotations

import logging
import re
from functools import lru_cache

import numpy as np
import spacy
import torch
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoModel, AutoModelForTokenClassification, AutoTokenizer, pipeline


logger = logging.getLogger(__name__)


class NLPService:
    def __init__(self) -> None:
        self._spacy_model = None
        self._summarizer = None
        self._legal_tokenizer = None
        self._legal_model = None
        self._ner_pipeline = None

    def get_spacy_model(self):
        if self._spacy_model is None:
            try:
                self._spacy_model = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy model en_core_web_sm is not installed. Falling back to blank English pipeline.")
                self._spacy_model = spacy.blank("en")
            if "sentencizer" not in self._spacy_model.pipe_names:
                self._spacy_model.add_pipe("sentencizer")
        return self._spacy_model

    def get_summarizer(self):
        if self._summarizer is None:
            self._summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                tokenizer="facebook/bart-large-cnn",
                framework="pt",
            )
        return self._summarizer

    def get_legal_bert(self):
        if self._legal_tokenizer is None or self._legal_model is None:
            self._legal_tokenizer = AutoTokenizer.from_pretrained("nlpaueb/legal-bert-base-uncased")
            self._legal_model = AutoModel.from_pretrained("nlpaueb/legal-bert-base-uncased")
            self._legal_model.eval()
        return self._legal_tokenizer, self._legal_model

    def get_ner_pipeline(self):
        if self._ner_pipeline is None:
            tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
            model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")
            self._ner_pipeline = pipeline(
                "token-classification",
                model=model,
                tokenizer=tokenizer,
                aggregation_strategy="simple",
            )
        return self._ner_pipeline

    @lru_cache(maxsize=32)
    def embed_text(self, text: str) -> np.ndarray:
        tokenizer, model = self.get_legal_bert()
        inputs = tokenizer(
            text[:4096],
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512,
        )
        with torch.no_grad():
            outputs = model(**inputs)
        embedding = outputs.last_hidden_state.mean(dim=1).squeeze(0).cpu().numpy()
        return embedding

    def safe_ner(self, text: str) -> list[dict]:
        try:
            ner = self.get_ner_pipeline()
            return ner(text[:4000])
        except Exception as exc:
            logger.warning("Falling back to spaCy entities: %s", exc)
            doc = self.get_spacy_model()(text)
            return [{"word": ent.text, "entity_group": ent.label_} for ent in doc.ents]

    def similarity(self, left: str, right: str) -> float:
        try:
            left_vec = self.embed_text(left)
            right_vec = self.embed_text(right)
            score = cosine_similarity([left_vec], [right_vec])[0][0]
            return float(max(0.0, min(1.0, score)))
        except Exception as exc:
            logger.warning("Falling back to lexical similarity: %s", exc)
            return self._lexical_similarity(left, right)

    def _lexical_similarity(self, left: str, right: str) -> float:
        left_tokens = set(re.findall(r"\w+", left.lower()))
        right_tokens = set(re.findall(r"\w+", right.lower()))
        if not left_tokens or not right_tokens:
            return 0.0
        return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)

    def safe_summarize(self, text: str, max_length: int = 180, min_length: int = 60) -> str:
        if len(text.split()) < 90:
            return text.strip()
        try:
            summarizer = self.get_summarizer()
            result = summarizer(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False,
                truncation=True,
            )
            return result[0]["summary_text"].strip()
        except Exception as exc:
            logger.warning("Falling back to extractive summary: %s", exc)
            return self.extractive_summary(text)

    def extractive_summary(self, text: str, sentence_count: int = 4) -> str:
        nlp = self.get_spacy_model()
        doc = nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        if not sentences:
            return text[:1000]
        return " ".join(sentences[:sentence_count])


nlp_service = NLPService()
