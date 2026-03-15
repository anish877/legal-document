import unittest
from unittest.mock import patch

try:
    from backend.services.document_service import DocumentService
except ModuleNotFoundError as exc:
    DocumentService = None
    DOCUMENT_SERVICE_IMPORT_ERROR = str(exc)
else:
    DOCUMENT_SERVICE_IMPORT_ERROR = ""


class _FakePage:
    def __init__(self, text: str) -> None:
        self._text = text

    def get_text(self, mode: str) -> str:
        return self._text


class _FakePdf:
    def __init__(self, pages):
        self._pages = pages

    def __iter__(self):
        return iter(self._pages)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@unittest.skipIf(DocumentService is None, f"document service dependencies unavailable: {DOCUMENT_SERVICE_IMPORT_ERROR}")
class DocumentServiceTests(unittest.TestCase):
    def test_pdf_processing_only_ocrs_low_text_pages(self):
        service = DocumentService()
        fake_pdf = _FakePdf(
            [
                _FakePage("This page already has enough machine-readable text to skip OCR entirely."),
                _FakePage("Too short"),
                _FakePage(""),
            ]
        )

        with patch("backend.services.document_service.fitz.open", return_value=fake_pdf):
            with patch.object(service, "_ocr_page", side_effect=["OCR replacement for page two", "OCR replacement for page three"]) as ocr_page:
                parsed = service._extract_pdf_text(b"fake-pdf")

        self.assertEqual(ocr_page.call_count, 2)
        self.assertEqual(parsed["pages"], 3)
        self.assertTrue(parsed["scanned_pdf"])
        self.assertEqual(parsed["page_details"][0]["mode"], "text")
        self.assertEqual(parsed["page_details"][1]["mode"], "ocr")
        self.assertEqual(parsed["page_details"][2]["mode"], "ocr")
        self.assertIn("OCR replacement for page two", parsed["text"])


if __name__ == "__main__":
    unittest.main()
