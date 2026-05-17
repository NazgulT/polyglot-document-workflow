# app/extractors/pdf.py

import io
import fitz  # PyMuPDF

from app.extractors.base import TextExtractor, ExtractionError


class PDFExtractor:
    """
    Extract text from PDF bytes using PyMuPDF.

    PyMuPDF is preferred over pdfminer / pypdf because:
    - It handles malformed PDFs without crashing
    - It respects reading order across multi-column layouts
    - No Java runtime dependency (unlike Tika)
    """

    def extract(self, data: bytes) -> str:
        try:
            doc = fitz.open(stream=io.BytesIO(data), filetype="pdf")
        except Exception as exc:
            raise ExtractionError(f"Failed to open PDF: {exc}") from exc

        pages: list[str] = []
        for page_num, page in enumerate(doc):
            try:
                text = page.get_text("text")   # "text" mode preserves reading order
                pages.append(text)
            except Exception as exc:
                # Log the bad page but don't abort the whole document
                raise ExtractionError(
                    f"Failed to extract page {page_num}: {exc}"
                ) from exc

        doc.close()

        full_text = "\n".join(pages).strip()

        if not full_text:
            raise ExtractionError(
                "PDF produced no extractable text. "
                "It may be a scanned image — OCR support is out of scope for Step 1."
            )

        return full_text