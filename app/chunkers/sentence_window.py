from typing import List, Dict

import nltk
from nltk.tokenize import sent_tokenize

nltk.download("punkt", quiet=True)


class SentenceWindowChunker:
    def __init__(self, window_size: int = 5):
        self.window_size = window_size

    def chunk(self, text: str) -> List[Dict[str, int]]:
        sentences = sent_tokenize(text)
        chunks: List[Dict[str, int]] = []

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
            chunks.append({"text": chunk_text, "char_offset": char_offset})

        return chunks
