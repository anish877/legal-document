from __future__ import annotations

import re
from functools import lru_cache

from backend.services.nlp_service import nlp_service


MAX_CLAUSE_CHARS = 12000


class LegalClauseDetector:
    whitespace_pattern = re.compile(r"[ \t]+")
    repeated_newlines_pattern = re.compile(r"\n{3,}")
    page_number_pattern = re.compile(r"(?im)^\s*(?:page\s+)?\d+(?:\s+of\s+\d+)?\s*$")

    clause_config = {
        "payment_clause": {
            "label": "Payment Clause",
            "patterns": [r"(?i)\bpayment terms?\b", r"(?i)\binvoice\b", r"(?i)\bfees?\b", r"(?i)\bconsideration\b"],
            "prototype": "This clause defines fees, invoicing, payment deadlines, late charges, and financial obligations.",
        },
        "confidentiality_clause": {
            "label": "Confidentiality Clause",
            "patterns": [r"(?i)\bconfidential(?:ity)?\b", r"(?i)\bnon-disclosure\b", r"(?i)\bproprietary information\b"],
            "prototype": "This clause protects confidential information and restricts disclosure, sharing, or misuse.",
        },
        "termination_clause": {
            "label": "Termination Clause",
            "patterns": [r"(?i)\btermination\b", r"(?i)\bmaterial breach\b", r"(?i)\bnotice period\b", r"(?i)\bsurvival\b"],
            "prototype": "This clause explains termination rights, cure periods, breach consequences, and surviving duties.",
        },
        "governing_law_clause": {
            "label": "Governing Law Clause",
            "patterns": [r"(?i)\bgoverning law\b", r"(?i)\bjurisdiction\b", r"(?i)\bvenue\b", r"(?i)\bdispute resolution\b"],
            "prototype": "This clause identifies governing law, forum, jurisdiction, venue, and dispute resolution procedures.",
        },
    }

    verdict_patterns = {
        "Petition Allowed": [r"(?i)\bpetition\s+is\s+allowed\b", r"(?i)\bappeal\s+is\s+allowed\b", r"(?i)\bsuit\s+is\s+decreed\b"],
        "Petition Dismissed": [r"(?i)\bpetition\s+is\s+dismissed\b", r"(?i)\bappeal\s+is\s+dismissed\b", r"(?i)\bsuit\s+is\s+dismissed\b"],
        "Partly Allowed": [r"(?i)\bpartly\s+allowed\b", r"(?i)\ballowed\s+in\s+part\b", r"(?i)\bpartially\s+granted\b"],
        "Settled / Disposed": [r"(?i)\bdisposed\s+of\b", r"(?i)\bsettled\s+between\s+the\s+parties\b", r"(?i)\bcompromise\s+decree\b"],
    }

    def preprocess_text(self, text: str) -> str:
        lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                lines.append("")
                continue
            if self.page_number_pattern.match(stripped):
                continue
            lines.append(self.whitespace_pattern.sub(" ", stripped))

        normalized = "\n".join(lines)
        normalized = self.repeated_newlines_pattern.sub("\n\n", normalized)
        return normalized.strip()

    @lru_cache(maxsize=64)
    def _cached_clause_analysis(self, normalized_text: str) -> tuple[tuple[str, tuple], ...]:
        limited_text = normalized_text[:MAX_CLAUSE_CHARS]
        sentences = self._sentences(limited_text)
        results: dict[str, dict] = {}

        for clause_name, config in self.clause_config.items():
            evidence = self._find_evidence(sentences, config["patterns"])
            matched_sentence = evidence[0] if evidence else ""
            evidence_text = " ".join(evidence[:3]) if evidence else limited_text[:1500]
            semantic_score = nlp_service.similarity(evidence_text, config["prototype"])
            keyword_score = min(1.0, len(evidence) / 3) if evidence else 0.0
            confidence = round(max(keyword_score, semantic_score), 2)

            results[clause_name] = {
                "clause": config["label"],
                "present": bool(evidence) or confidence >= 0.5,
                "text": matched_sentence,
                "evidence": evidence[:3],
                "confidence": confidence,
            }

        return tuple((name, tuple(result.items())) for name, result in results.items())

    def extract_clauses(self, text: str) -> dict:
        normalized_text = self.preprocess_text(text)
        cached = self._cached_clause_analysis(normalized_text)
        results: dict[str, dict] = {}
        for clause_name, items in cached:
            data = dict(items)
            data["evidence"] = list(data["evidence"])
            results[clause_name] = data
        return results

    def detect_final_verdict(self, text: str) -> str:
        normalized_text = self.preprocess_text(text)
        tail = normalized_text[-5000:] if len(normalized_text) > 5000 else normalized_text

        for verdict, patterns in self.verdict_patterns.items():
            if any(re.search(pattern, tail) for pattern in patterns):
                return verdict

        if nlp_service.similarity(tail, "The petition is allowed and relief is granted.") >= 0.62:
            return "Likely Allowed"
        if nlp_service.similarity(tail, "The petition is dismissed and no relief is granted.") >= 0.62:
            return "Likely Dismissed"
        return "Verdict not clearly detected"

    def _find_evidence(self, sentences: list[str], patterns: list[str]) -> list[str]:
        matches: list[str] = []
        for sentence in sentences:
            if any(re.search(pattern, sentence) for pattern in patterns):
                matches.append(sentence.strip())
        return matches

    def _sentences(self, text: str) -> list[str]:
        doc = nlp_service.get_spacy_model()(text)
        return [sent.text.strip() for sent in doc.sents if sent.text.strip()]


legal_clause_detector = LegalClauseDetector()


def extract_clauses(text: str) -> dict:
    return legal_clause_detector.extract_clauses(text)


def detect_final_verdict(text: str) -> str:
    return legal_clause_detector.detect_final_verdict(text)
