from __future__ import annotations

import re

from backend.services.text_normalizer import text_normalizer


class ClauseEngine:
    clause_config = {
        "payment_clause": {
            "label": "Payment Clause",
            "patterns": [r"(?i)\bpayment terms?\b", r"(?i)\binvoice\b", r"(?i)\bfees?\b", r"(?i)\bconsideration\b"],
        },
        "confidentiality_clause": {
            "label": "Confidentiality Clause",
            "patterns": [r"(?i)\bconfidential(?:ity)?\b", r"(?i)\bnon-disclosure\b", r"(?i)\bproprietary information\b"],
        },
        "termination_clause": {
            "label": "Termination Clause",
            "patterns": [r"(?i)\btermination\b", r"(?i)\bmaterial breach\b", r"(?i)\bnotice period\b", r"(?i)\bsurvival\b"],
        },
        "governing_law_clause": {
            "label": "Governing Law Clause",
            "patterns": [r"(?i)\bgoverning law\b", r"(?i)\bjurisdiction\b", r"(?i)\bvenue\b", r"(?i)\bdispute resolution\b"],
        },
    }

    def extract(self, text: str) -> dict:
        sentences = text_normalizer.split_sentences(text)
        paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
        results: dict[str, dict] = {}

        for clause_name, config in self.clause_config.items():
            evidence = self._find_evidence(sentences, config["patterns"])
            heading_hit = self._find_heading(paragraphs, config["patterns"])
            confidence = self._confidence(evidence_count=len(evidence), heading_hit=bool(heading_hit))
            first_match = evidence[0] if evidence else heading_hit or ""
            results[clause_name] = {
                "clause": config["label"],
                "present": bool(evidence or heading_hit),
                "text": first_match,
                "evidence": evidence[:3],
                "confidence": confidence,
            }

        return results

    def _find_evidence(self, sentences: list[str], patterns: list[str]) -> list[str]:
        matches: list[str] = []
        for sentence in sentences:
            if any(re.search(pattern, sentence) for pattern in patterns):
                matches.append(sentence.strip())
        return matches

    def _find_heading(self, paragraphs: list[str], patterns: list[str]) -> str:
        for paragraph in paragraphs:
            if len(paragraph) > 160:
                continue
            if any(re.search(pattern, paragraph) for pattern in patterns):
                return paragraph
        return ""

    def _confidence(self, evidence_count: int, heading_hit: bool) -> float:
        if evidence_count == 0 and not heading_hit:
            return 0.0
        confidence = 0.35 + min(0.45, evidence_count * 0.2) + (0.2 if heading_hit else 0.0)
        return round(min(1.0, confidence), 2)


clause_engine = ClauseEngine()
