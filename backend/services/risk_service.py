from __future__ import annotations


class RiskService:
    def analyze_risks(self, text: str, clauses: dict, entities: dict, verdict: str) -> list[dict]:
        risks: list[dict] = []
        lowered = text.lower()

        missing = {
            "payment_clause": "Payment clause is missing, which can create billing and collection disputes.",
            "confidentiality_clause": "Confidentiality clause is missing, which increases disclosure risk.",
            "termination_clause": "Termination clause is missing, which weakens exit rights and remedies.",
            "governing_law_clause": "Governing law clause is missing, which can create jurisdiction uncertainty.",
        }

        for clause_name, description in missing.items():
            if not clauses[clause_name]["present"]:
                risks.append(
                    {
                        "title": clause_name.replace("_", " ").title(),
                        "level": "high",
                        "description": description,
                        "recommendation": f"Add a clear {clause_name.replace('_', ' ')} with enforceable language.",
                    }
                )

        if "indemn" not in lowered and "liability" in lowered:
            risks.append(
                {
                    "title": "Liability Allocation Gap",
                    "level": "medium",
                    "description": "Liability is discussed without a matching indemnity or limitation framework.",
                    "recommendation": "Add indemnity, limitation of liability, and carve-out language.",
                }
            )

        if "sole discretion" in lowered or "at any time without cause" in lowered:
            risks.append(
                {
                    "title": "Potentially Unbalanced Agreement",
                    "level": "medium",
                    "description": "One-sided discretionary wording may create unfair contract risk.",
                    "recommendation": "Review unilateral rights and add reciprocal obligations where appropriate.",
                }
            )

        if not entities.get("parties"):
            risks.append(
                {
                    "title": "Unclear Party Identification",
                    "level": "medium",
                    "description": "The document does not clearly expose contracting or litigating parties.",
                    "recommendation": "Verify party names, roles, and signature blocks.",
                }
            )

        if verdict == "Verdict not clearly detected" and any(word in lowered for word in ["court", "judge", "petition"]):
            risks.append(
                {
                    "title": "Outcome Ambiguity",
                    "level": "low",
                    "description": "The judgment outcome was not clearly detected from the extracted text.",
                    "recommendation": "Check whether the concluding pages were extracted correctly or require OCR cleanup.",
                }
            )

        return risks


risk_service = RiskService()
