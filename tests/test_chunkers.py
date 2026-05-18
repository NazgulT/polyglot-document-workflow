# tests/test_chunkers.py
#
# Unit tests for chunker classes — no DB required.

from nltk.tokenize import sent_tokenize

from app.chunkers.fixed import FixedSizeChunker
from app.chunkers.recursive import RecursiveCharacterChunker
from app.chunkers.sentence_window import SentenceWindowChunker

# ── Test fixtures ─────────────────────────────────────────────────────────────

# 1 000-char string with no whitespace so .strip() never shifts window boundaries.
DENSE_TEXT = "ABCDEFGHIJ" * 100

SAMPLE_TEXT = (
    "The quick brown fox jumps over the lazy dog. "
    "Pack my box with five dozen liquor jugs. "
    "How vexingly quick daft zebras jump. "
    "The five boxing wizards jump quickly. "
    "Sphinx of black quartz judge my vow."
)


def _texts(chunker, text: str) -> list[str]:
    """Return a flat list of chunk strings regardless of chunker return type."""
    if isinstance(chunker, FixedSizeChunker):
        return [c["text"] for c in chunker.split_text(text)]
    result = chunker.chunk(text)
    if result and isinstance(result[0], dict):
        return [c["text"] for c in result]
    return list(result)  # RecursiveCharacterChunker returns plain strings


# ── Unit tests ────────────────────────────────────────────────────────────────

def test_fixed_chunker_produces_correct_overlap():
    chunker = FixedSizeChunker(chunk_size=200, chunk_overlap=50)
    chunks = chunker.split_text(DENSE_TEXT)

    assert len(chunks) >= 2, "Need at least two chunks to verify overlap"

    for i in range(len(chunks) - 1):
        shared_tail = chunks[i]["text"][-50:]
        shared_head = chunks[i + 1]["text"][:50]
        assert shared_tail == shared_head, (
            f"Chunk {i} tail != chunk {i + 1} head — overlap not preserved"
        )


def test_fixed_chunker_char_offset_is_correct():
    chunker = FixedSizeChunker(chunk_size=200, chunk_overlap=50)
    chunks = chunker.split_text(DENSE_TEXT)

    for chunk in chunks:
        offset = chunk["char_offset"]
        text_slice = DENSE_TEXT[offset : offset + len(chunk["text"])]
        assert text_slice == chunk["text"], (
            f"char_offset {offset} does not point to chunk text in original"
        )


def test_sentence_window_chunks_are_not_empty():
    chunker = SentenceWindowChunker(window_size=3)
    chunks = chunker.chunk(SAMPLE_TEXT)

    assert len(chunks) > 0, "SentenceWindowChunker produced no chunks"
    for chunk in chunks:
        assert chunk["text"].strip() != "", "Chunk contains only whitespace"


def test_all_chunkers_cover_full_document():
    sentences = sent_tokenize(SAMPLE_TEXT)
    # chunk_size generous enough that no individual sentence is split in half,
    # so every sentence must appear intact in at least one chunk.
    chunkers = [
        FixedSizeChunker(chunk_size=300, chunk_overlap=0),
        SentenceWindowChunker(window_size=2),
        RecursiveCharacterChunker(chunk_size=300),
    ]

    for chunker in chunkers:
        texts = _texts(chunker, SAMPLE_TEXT)
        for sentence in sentences:
            found = any(sentence in t for t in texts)
            assert found, (
                f"{chunker.__class__.__name__} silently dropped sentence: {sentence!r}"
            )


def test_token_count_is_populated():
    chunker = FixedSizeChunker(chunk_size=200, chunk_overlap=0)
    chunks = chunker.split_text(SAMPLE_TEXT)

    assert len(chunks) > 0, "No chunks produced"
    for chunk in chunks:
        assert chunk["token_count"] > 0, (
            f"Chunk has token_count={chunk['token_count']!r}, expected > 0"
        )
