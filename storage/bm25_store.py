from rank_bm25 import BM25Okapi
from typing import List, Dict
import re


class BM25Store:

    def __init__(self):
        self.docs = []
        self.meta = []
        self.bm25 = None
        self.tokens = []

    def _tokenize(self, text: str):
        text = text.lower()
        text = re.sub(r"[^a-zа-я0-9 ]", " ", text)
        return text.split()

    def rebuild(self, documents: List[Dict]):
        """
        documents = [{text, metadata}]
        """

        self.docs = [d["text"] for d in documents]
        self.meta = [d.get("metadata", {}) for d in documents]

        self.tokens = [self._tokenize(t) for t in self.docs]
        self.bm25 = BM25Okapi(self.tokens)

    def search(self, query: str, k: int = 5):

        if not self.bm25:
            return []

        q = self._tokenize(query)
        scores = self.bm25.get_scores(q)

        ranked = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True
        )[:k]

        return [
            {
                "text": self.docs[i],
                "metadata": self.meta[i],
                "score": float(score)
            }
            for i, score in ranked
        ]