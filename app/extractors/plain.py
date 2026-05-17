# app/extractors/plain.py

from app.extractors.base import ExtractionError


class PlainTextExtractor:
    """
    Decode raw bytes as UTF-8 text, with a fallback to latin-1.

    The fallback prevents hard failures on legacy files that were never
    properly encoded. We normalise to UTF-8 before storing.
    """

    def extract(self, data: bytes) -> str:
        for encoding in ("utf-8", "latin-1"):
            try:
                text = data.decode(encoding).strip()
                if text:
                    return text
            except (UnicodeDecodeError, ValueError):
                continue

        raise ExtractionError("Could not decode plain text file with utf-8 or latin-1.")