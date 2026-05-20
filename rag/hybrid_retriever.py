from typing import List, Dict
from storage.vector_store import VectorStore
from storage.bm25_store import BM25Store

class HybridRetriever:
    def __init__(self, vector_store: VectorStore, bm25_store: BM25Store):
        self.vs = vector_store
        self.bm25 = bm25_store

    def rrf_fusion(self, dense, sparse, k=60):
        """
        Reciprocal Rank Fusion
        """
        scores = {}

        def add_results(results, weight=1.0):
            for rank, item in enumerate(results):
                key = item["text"]
                scores[key] = scores.get(key, 0) + weight * (1 / (k + rank + 1))

        add_results(dense, weight=1.0)
        add_results(sparse, weight=0.8)

        fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return fused

    def retrieve(self, query: str, limit: int = 5):

        # 1. dense (Chroma)
        dense_messages = self.vs.search_messages(query, limit=limit)
        dense_tasks = self.vs.search_similar_tasks(query, limit=limit)

        dense = [
            {"text": d["text"], "metadata": d["metadata"]}
            for d in dense_messages + dense_tasks
        ]

        # 2. bm25 (по всей базе)
        sparse = self.bm25.search(query, k=limit)

        # 3. fusion
        fused = self.rrf_fusion(dense, sparse)

        # 4. rebuild final context objects
        final = []
        for text, score in fused[:limit]:
            final.append({
                "text": text,
                "score": score
            })

        return final