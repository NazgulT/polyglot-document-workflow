# app/extractors/__init__.py

import magic

from app.extractors.base import TextExtractor, ExtractionError
from app.extractors.pdf import PDFExtractor
from app.extractors.docx import DocxExtractor
from app.extractors.plain import PlainTextExtractor


_REGISTRY: dict[str, TextExtractor] = {
    "application/pdf": PDFExtractor(),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocxExtractor(),
    "text/plain": PlainTextExtractor(),
}


def detect_mime_type(data: bytes) -> str:
    """
    Detect MIME type from the first bytes of the file.

    python-magic reads the file's magic bytes (the first ~262 bytes),
    which is how the Unix `file` command works. This cannot be spoofed
    by renaming a file — a .pdf extension on a .docx is caught here.
    """
    return magic.from_buffer(data, mime=True)


def get_extractor(mime_type: str) -> TextExtractor:
    """
    Return the appropriate TextExtractor for a given MIME type.
    Raises ExtractionError if the type is unsupported.
    """
    extractor = _REGISTRY.get(mime_type)
    if extractor is None:
        raise ExtractionError(
            f"No extractor registered for MIME type '{mime_type}'. "
            f"Supported: {list(_REGISTRY.keys())}"
        )
    return extractor