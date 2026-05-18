from sentence_transformers import SentenceTransformer


class LocalSentenceTransformerProvider:
    def __init__(self) -> None:
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self.model.encode(texts, batch_size=32, show_progress_bar=False).tolist()

    @property
    def dimensions(self) -> int:
        return 384
