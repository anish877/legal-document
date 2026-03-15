from __future__ import annotations

from io import BytesIO
from pathlib import Path

import fitz
from PIL import Image

from backend.utils.runtime import ENABLE_OCR

try:
    import pytesseract
except ImportError:  # pragma: no cover - exercised in lite deployments
    pytesseract = None


class DocumentService:
    allowed_extensions = {".pdf", ".txt"}

    async def parse_upload(self, filename: str, file_bytes: bytes) -> dict:
        extension = Path(filename).suffix.lower()
        if extension not in self.allowed_extensions:
            raise ValueError("Unsupported file type. Upload a PDF or TXT file.")

        if extension == ".txt":
            text = file_bytes.decode("utf-8", errors="ignore")
            return {
                "text": text,
                "pages": None,
                "file_type": "text",
                "scanned_pdf": False,
            }

        return self._extract_pdf_text(file_bytes)

    def _extract_pdf_text(self, file_bytes: bytes) -> dict:
        pdf = fitz.open(stream=file_bytes, filetype="pdf")
        page_texts: list[str] = []
        low_text_pages = 0

        for page in pdf:
            text = page.get_text("text").strip()
            if len(text) < 80:
                low_text_pages += 1
            page_texts.append(text)

        scanned_pdf = len(page_texts) > 0 and low_text_pages / len(page_texts) >= 0.5

        if scanned_pdf and ENABLE_OCR and pytesseract is not None:
            page_texts = [self._ocr_page(page) for page in pdf]

        return {
            "text": "\n\n".join(page_texts),
            "pages": len(page_texts),
            "file_type": "pdf",
            "scanned_pdf": scanned_pdf,
        }

    def _ocr_page(self, page: fitz.Page) -> str:
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        image = Image.open(BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(image)


document_service = DocumentService()
