# app/extractors/base.py

from typing import Protocol, runtime_checkable


@runtime_checkable
class TextExtractor(Protocol):
    """
    Contract every concrete extractor must satisfy.

    Accepts raw bytes, returns clean UTF-8 text.
    Raises ExtractionError on unrecoverable failure.
    """

    def extract(self, data: bytes) -> str:
        ...


class ExtractionError(Exception):
    """Raised when text cannot be extracted from a document."""