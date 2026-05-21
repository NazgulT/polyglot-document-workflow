from typing import List, Dict
import uuid

import nltk
from nltk.tokenize import sent_tokenize

from app.schemas.chunk import DocumentChunk

nltk.download("punkt", quiet=True)


class SentenceWindowChunker:
    def __init__(self, window_size: int = 5):
        self.window_size = window_size

    def split(self, text: str, doc_id: uuid.UUID) -> List[DocumentChunk]:
        sentences = sent_tokenize(text)
        chunks: List[DocumentChunk] = []

        current_offset = 0
        for start in range(len(sentences) - self.window_size + 1):
            window_sentences = sentences[start : start + self.window_size]
            chunk_text = " ".join(window_sentences)
            first_sentence = window_sentences[0]

            try:
                char_offset = text.index(first_sentence, current_offset)
            except ValueError:
                char_offset = text.find(first_sentence, current_offset)
                if char_offset == -1:
                    char_offset = text.find(first_sentence)
                    if char_offset == -1:
                        char_offset = 0

            current_offset = char_offset + len(first_sentence)
            chunks.append(DocumentChunk(text=chunk_text, char_offset=char_offset, token_count=0, doc_id=doc_id))

        return chunks
