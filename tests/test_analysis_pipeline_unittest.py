import unittest
from unittest.mock import patch

try:
    from backend.services.analysis_pipeline import AnalysisPipeline
    from backend.services.analysis_types import NormalizedDocument, SummaryArtifacts
    from backend.services.summary_engine import SummaryEngine
except ModuleNotFoundError as exc:
    AnalysisPipeline = None
    SummaryEngine = None
    NormalizedDocument = None
    SummaryArtifacts = None
    PIPELINE_IMPORT_ERROR = str(exc)
else:
    PIPELINE_IMPORT_ERROR = ""

try:
    from fastapi.testclient import TestClient
    from backend.main import app
except ModuleNotFoundError as exc:
    TestClient = None
    app = None
    FASTAPI_IMPORT_ERROR = str(exc)
else:
    FASTAPI_IMPORT_ERROR = ""


class _CountingNormalizer:
    def __init__(self) -> None:
        self.calls = 0

    def normalize_document(self, text: str) -> NormalizedDocument:
        self.calls += 1
        cleaned = "Cleaned contract text with payment clause."
        return NormalizedDocument(
            text=cleaned,
            sentences=("Cleaned contract text with payment clause.",),
            chunks=(cleaned,),
        )


class _RecordingSummary:
    def __init__(self) -> None:
        self.received = []

    def summarize(self, document: NormalizedDocument) -> SummaryArtifacts:
        self.received.append(document.text)
        return SummaryArtifacts(
            summary="Cleaned contract text with payment clause.",
            short_summary="Cleaned contract text with payment clause.",
            chunk_summaries=("Cleaned contract text with payment clause.",),
        )

    def infer_document_type(self, text: str) -> str:
        return "Legal Agreement"

    def extract_locations(self, text: str) -> list[str]:
        return []

    def extract_financial_terms(self, text: str) -> list[str]:
        return []

    def extract_clause_highlights(self, text: str) -> list[str]:
        return ["Payment Clause"]


class _RecordingEntities:
    def __init__(self) -> None:
        self.received = []

    def extract(self, text: str) -> dict:
        self.received.append(text)
        return {
            "judges": [],
            "parties": [{"name": "ABC Ltd.", "role": "First Party"}],
            "locations": [],
            "dates": [],
            "case_numbers": [],
            "money": [],
            "monetary_values": [],
        }


class _RecordingClauses:
    def __init__(self) -> None:
        self.received = []

    def extract(self, text: str) -> dict:
        self.received.append(text)
        return {
            "payment_clause": {
                "clause": "Payment Clause",
                "present": True,
                "text": text,
                "evidence": [text],
                "confidence": 0.9,
            },
            "confidentiality_clause": {
                "clause": "Confidentiality Clause",
                "present": False,
                "text": "",
                "evidence": [],
                "confidence": 0.0,
            },
            "termination_clause": {
                "clause": "Termination Clause",
                "present": False,
                "text": "",
                "evidence": [],
                "confidence": 0.0,
            },
            "governing_law_clause": {
                "clause": "Governing Law Clause",
                "present": False,
                "text": "",
                "evidence": [],
                "confidence": 0.0,
            },
        }


class _RecordingVerdict:
    def __init__(self) -> None:
        self.received = []

    def detect(self, text: str) -> str:
        self.received.append(text)
        return "Verdict not clearly detected"


@unittest.skipIf(AnalysisPipeline is None or SummaryEngine is None, f"analysis pipeline dependencies unavailable: {PIPELINE_IMPORT_ERROR}")
class AnalysisPipelineTests(unittest.TestCase):
    def test_pipeline_cleans_once_and_reuses_normalized_text(self):
        normalizer = _CountingNormalizer()
        summary = _RecordingSummary()
        entities = _RecordingEntities()
        clauses = _RecordingClauses()
        verdicts = _RecordingVerdict()
        pipeline = AnalysisPipeline(
            normalizer=normalizer,
            summary=summary,
            entities=entities,
            clauses=clauses,
            verdicts=verdicts,
        )

        result = pipeline.analyze(" messy raw input ")

        self.assertEqual(normalizer.calls, 1)
        self.assertEqual(summary.received, ["Cleaned contract text with payment clause."])
        self.assertEqual(entities.received, ["Cleaned contract text with payment clause."])
        self.assertEqual(clauses.received, ["Cleaned contract text with payment clause."])
        self.assertEqual(verdicts.received, ["Cleaned contract text with payment clause."])
        self.assertEqual(result.cleaned_text, "Cleaned contract text with payment clause.")

    def test_summary_engine_default_path_skips_abstractive_adapter(self):
        engine = SummaryEngine()
        document = NormalizedDocument(
            text="This agreement sets payment terms. It also sets a notice period for termination.",
            sentences=(
                "This agreement sets payment terms.",
                "It also sets a notice period for termination.",
            ),
            chunks=("This agreement sets payment terms. It also sets a notice period for termination.",),
        )

        with patch.object(engine, "_abstractive_summary", side_effect=AssertionError("should not be called")):
            summary = engine.summarize(document)

        self.assertTrue(summary.summary)

    def test_api_contracts_remain_stable_for_text_documents(self):
        if TestClient is None or app is None:
            self.skipTest(f"fastapi dependencies unavailable: {FASTAPI_IMPORT_ERROR}")

        client = TestClient(app)
        sample_text = (
            "Service Agreement\n\n"
            "First Party: ABC Solutions Ltd\n"
            "Second Party: XYZ Services Ltd\n\n"
            "Payment terms require invoices to be paid within 15 days.\n"
            "This agreement is governed by the laws of Delhi."
        )

        upload_response = client.post(
            "/upload-document",
            files={"file": ("sample.txt", sample_text.encode("utf-8"), "text/plain")},
        )
        self.assertEqual(upload_response.status_code, 200)
        upload_payload = upload_response.json()

        self.assertEqual(
            set(upload_payload.keys()),
            {
                "extracted_text",
                "summary",
                "detailed_summary",
                "entities",
                "insights",
                "clauses",
                "verdict",
                "risks",
                "metadata",
                "debug",
            },
        )
        self.assertEqual(upload_payload["metadata"]["file_type"], "text")
        self.assertIn("metrics", upload_payload["debug"])
        self.assertIn("parse", upload_payload["debug"]["metrics"]["durations"])
        self.assertEqual(upload_payload["debug"]["metrics"]["durations"]["ocr"], 0.0)

        summarize_payload = client.post("/summarize", json={"text": sample_text}).json()
        entities_payload = client.post("/extract-entities", json={"text": sample_text}).json()
        clauses_payload = client.post("/extract-clauses", json={"text": sample_text}).json()
        risks_payload = client.post("/analyze-risks", json={"text": sample_text}).json()

        self.assertEqual(set(summarize_payload.keys()), {"summary", "detailed_summary", "verdict"})
        self.assertEqual(set(entities_payload.keys()), {"entities"})
        self.assertEqual(set(clauses_payload.keys()), {"clauses", "verdict"})
        self.assertEqual(set(risks_payload.keys()), {"risks"})


if __name__ == "__main__":
    unittest.main()
