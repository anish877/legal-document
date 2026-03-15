from __future__ import annotations

import re


class VerdictEngine:
    verdict_patterns = {
        "Petition Allowed": [r"(?i)\bpetition\s+is\s+allowed\b", r"(?i)\bappeal\s+is\s+allowed\b", r"(?i)\bsuit\s+is\s+decreed\b"],
        "Petition Dismissed": [r"(?i)\bpetition\s+is\s+dismissed\b", r"(?i)\bappeal\s+is\s+dismissed\b", r"(?i)\bsuit\s+is\s+dismissed\b"],
        "Partly Allowed": [r"(?i)\bpartly\s+allowed\b", r"(?i)\ballowed\s+in\s+part\b", r"(?i)\bpartially\s+granted\b"],
        "Settled / Disposed": [r"(?i)\bdisposed\s+of\b", r"(?i)\bsettled\s+between\s+the\s+parties\b", r"(?i)\bcompromise\s+decree\b"],
    }

    def detect(self, text: str) -> str:
        tail = text[-5000:] if len(text) > 5000 else text

        for verdict, patterns in self.verdict_patterns.items():
            if any(re.search(pattern, tail) for pattern in patterns):
                return verdict

        lowered = tail.casefold()
        if ("petition" in lowered or "appeal" in lowered) and "allowed" in lowered and "dismissed" not in lowered:
            return "Likely Allowed"
        if ("petition" in lowered or "appeal" in lowered) and "dismissed" in lowered:
            return "Likely Dismissed"
        if "disposed" in lowered or "settled" in lowered or "compromise" in lowered:
            return "Settled / Disposed"
        return "Verdict not clearly detected"


verdict_engine = VerdictEngine()
