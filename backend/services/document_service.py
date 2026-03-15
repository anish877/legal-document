from __future__ import annotations

from io import BytesIO
from pathlib import Path
from time import perf_counter

import fitz
import pytesseract
from PIL import Image

from backend.services.analysis_config import analysis_config


class DocumentService:
    allowed_extensions = {".pdf", ".txt"}

    async def parse_upload(self, filename: str, file_bytes: bytes, progress_callback=None) -> dict:
        extension = Path(filename).suffix.lower()
        if extension not in self.allowed_extensions:
            raise ValueError("Unsupported file type. Upload a PDF or TXT file.")

        if extension == ".txt":
            text = file_bytes.decode("utf-8", errors="ignore")
            self._emit_progress(
                progress_callback,
                stage="extract",
                message="Loaded text document.",
                progress=0.22,
                detail={"file_type": "text"},
            )
            return {
                "text": text,
                "pages": None,
                "file_type": "text",
                "scanned_pdf": False,
                "page_details": [],
                "ocr_seconds": 0.0,
            }

        return self._extract_pdf_text(file_bytes, progress_callback=progress_callback)

    def _extract_pdf_text(self, file_bytes: bytes, progress_callback=None) -> dict:
        page_texts: list[str] = []
        page_details: list[dict] = []
        low_text_pages = 0
        ocr_seconds = 0.0

        with fitz.open(stream=file_bytes, filetype="pdf") as pdf:
            total_pages = len(pdf)
            self._emit_progress(
                progress_callback,
                stage="extract",
                message=f"Opened PDF with {total_pages} pages.",
                progress=0.12,
                detail={"pages": total_pages},
            )
            for index, page in enumerate(pdf, start=1):
                extracted_text = page.get_text("text").strip()
                mode = "text"
                ocr_attempted = False
                ocr_text = ""

                if len(extracted_text) < analysis_config.low_text_threshold:
                    low_text_pages += 1
                    ocr_attempted = True
                    start = perf_counter()
                    ocr_text = self._ocr_page(page).strip()
                    ocr_seconds += perf_counter() - start
                    if len(ocr_text) > len(extracted_text):
                        extracted_text = ocr_text
                        mode = "ocr"

                page_texts.append(extracted_text)
                page_details.append(
                    {
                        "page": index,
                        "mode": mode,
                        "ocr_attempted": ocr_attempted,
                        "text_chars": len(extracted_text),
                    }
                )
                progress = 0.12 + (index / max(total_pages, 1)) * 0.22
                self._emit_progress(
                    progress_callback,
                    stage="extract",
                    message=f"Processed page {index} of {total_pages}.",
                    progress=min(progress, 0.34),
                    detail=page_details[-1],
                )

        page_count = len(page_texts)
        scanned_pdf = page_count > 0 and low_text_pages / page_count >= analysis_config.scanned_ratio_threshold

        return {
            "text": "\n\n".join(page_texts),
            "pages": page_count,
            "file_type": "pdf",
            "scanned_pdf": scanned_pdf,
            "page_details": page_details,
            "ocr_seconds": round(ocr_seconds, 4),
        }

    def _ocr_page(self, page: fitz.Page) -> str:
        pix = page.get_pixmap(matrix=fitz.Matrix(analysis_config.ocr_zoom, analysis_config.ocr_zoom), alpha=False)
        image = Image.open(BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(image)

    def _emit_progress(self, callback, stage: str, message: str, progress: float, detail: dict | None = None) -> None:
        if callback is None:
            return
        callback(
            {
                "stage": stage,
                "message": message,
                "progress": round(progress, 3),
                "detail": detail or {},
            }
        )


document_service = DocumentService()
