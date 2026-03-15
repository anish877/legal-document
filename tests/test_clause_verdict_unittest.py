import unittest

from backend.services.clause_engine import ClauseEngine
from backend.services.verdict_engine import VerdictEngine


class ClauseAndVerdictTests(unittest.TestCase):
    def test_clause_detection_uses_regex_evidence_only(self):
        engine = ClauseEngine()
        text = """
        Payment Terms:
        The client shall pay all invoice amounts within fifteen days.

        Confidentiality:
        Each party shall keep proprietary information confidential.
        """

        clauses = engine.extract(text)

        self.assertTrue(clauses["payment_clause"]["present"])
        self.assertTrue(clauses["confidentiality_clause"]["present"])
        self.assertFalse(clauses["termination_clause"]["present"])
        self.assertGreaterEqual(clauses["payment_clause"]["confidence"], 0.35)
        self.assertIn("invoice", clauses["payment_clause"]["text"].lower())

    def test_verdict_detection_uses_tail_heuristics(self):
        engine = VerdictEngine()
        text = """
        The court heard the parties.

        Accordingly, the petition is dismissed with no order as to costs.
        """

        verdict = engine.detect(text)

        self.assertEqual(verdict, "Petition Dismissed")


if __name__ == "__main__":
    unittest.main()
