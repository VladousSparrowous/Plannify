from rank_bm25 import BM25Okapi
import re
from typing import TypedDict, List, Dict, Any, Optional


import os
import re
import pickle
from rank_bm25 import BM25Okapi
from typing import TypedDict, List, Dict, Any, Optional

class BM25Store:
    def __init__(self, filepath: str = "data/bm25_store.pkl"):
        self.filepath = filepath
        self.docs = []
        self.meta = []
        self.bm25 = None
        self.load()  # Автоматическая загрузка при старте бота

    def _tokenize(self, text: str) -> List[str]:
        if not text:
            return []
        text = text.lower()
        text = re.sub(r"[^a-zа-я0-9 ]", " ", text)
        return text.split()

    def load(self):
        """Загрузка индекса с диска"""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'rb') as f:
                    data = pickle.load(f)
                    self.docs = data.get('docs', [])
                    self.meta = data.get('meta', [])
                    self.bm25 = data.get('bm25', None)
            except Exception as e:
                pass

    def save(self):
        """Сохранение индекса на диск"""
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        try:
            with open(self.filepath, 'wb') as f:
                pickle.dump({
                    'docs': self.docs,
                    'meta': self.meta,
                    'bm25': self.bm25
                }, f)
        except Exception as e:
            pass

    def rebuild(self, documents: List[Dict]):
        if not documents:
            self.docs = []
            self.meta = []
            self.bm25 = None
            self.save()
            return

        self.docs = [d["text"] for d in documents]
        self.meta = [d.get("metadata", {}) for d in documents]
        
        tokens = [self._tokenize(t) for t in self.docs]
        self.bm25 = BM25Okapi(tokens)
        self.save()  # Сохраняем актуальное состояние

    def search(self, query: str, k: int = 5) -> List[Dict]:
        if not self.bm25 or not self.docs:
            return []

        q_tokens = self._tokenize(query)
        if not q_tokens:
            return []

        scores = self.bm25.get_scores(q_tokens)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:k]

        return [
            {
                "text": self.docs[i],
                "metadata": self.meta[i],
                "score": float(score)
            }
            for i, score in ranked
        ]


class Normalizer:
    """Нормализация документов в единый формат"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        return " ".join(text.split()).strip()

    @staticmethod
    def enforce(doc: dict) -> dict:
        """Приводит документ к строгому контракту Document"""
        return {
            "id": doc.get("id", ""),
            "text": Normalizer.clean_text(doc.get("text", "")),
            "type": doc.get("type", "message"),
            "source": doc.get("source", "unknown"),
            "timestamp": doc.get("timestamp"),
            "link": doc.get("link"),
            "metadata": doc.get("metadata", {})
        }


class Document(TypedDict):
    id: str
    text: str
    type: str
    source: str
    timestamp: Optional[str]
    link: Optional[str]
    metadata: Dict[str, Any]