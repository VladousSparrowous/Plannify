from typing import List, Dict
from collections import defaultdict
from storage.vector_store import VectorStore
from storage.bm25_store import BM25Store
from collections import defaultdict

class HybridRetriever:
    def __init__(self, vector_store: VectorStore, bm25_store: BM25Store):
        self.vs = vector_store
        self.bm25 = bm25_store

    def rrf_fusion(self, dense: List[Dict], sparse: List[Dict], k: int = 60) -> List[tuple]:
        """
        Reciprocal Rank Fusion — объединение результатов плотного и разреженного поиска
        """
        scores = {}

        def add_results(results, weight=1.0):
            for rank, item in enumerate(results):
                key = item.get("text", "")
                if not key:
                    continue
                scores[key] = scores.get(key, 0) + weight * (1 / (k + rank + 1))

        add_results(dense, weight=1.0)
        add_results(sparse, weight=0.8)

        return sorted(scores.items(), key=lambda x: x[1], reverse=True)

    def retrieve(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Гибридный поиск: dense (Chroma) + sparse (BM25)
        """
        # 1. Плотный поиск (векторный)
        dense_messages = self.vs.search_messages(query, limit=limit * 2)  # берём больше для фьюжн
        dense_tasks = self.vs.search_similar_tasks(query, limit=limit * 2)

        dense = []
        for d in dense_messages + dense_tasks:
            dense.append({
                "text": d.get("text", ""),
                "metadata": d.get("metadata", {})
            })

        # 2. Разреженный поиск (BM25)
        sparse = self.bm25.search(query, k=limit * 2)

        # 3. RRF фьюжн
        fused = self.rrf_fusion(dense, sparse)

        # 4. Восстанавливаем полные объекты
        text_to_meta = {}
        for d in dense:
            text_to_meta[d["text"]] = d["metadata"]
        for s in sparse:
            text_to_meta[s["text"]] = s.get("metadata", {})

        final = []
        for text, score in fused[:limit]:
            final.append({
                "text": text,
                "score": score,
                "metadata": text_to_meta.get(text, {})
            })

        return final


# В rag/hybrid_retriever.py, класс ContextEngine

class ContextEngine:
    """Преобразует результаты поиска в структурированный контекст для LLM"""
    
    def build(self, query: str, results: List[Dict]) -> tuple:
        """
        Возвращает (context_text, sources_dict)
        где sources_dict = {номер: {"title": "...", "link": "..."}}
        """
        grouped = defaultdict(list)
        
        for r in results:
            meta = r.get("metadata", {})
            source = meta.get("source", "unknown")
            grouped[source].append(r)
        
        parts = []
        sources = {}  # {номер_источника: {"title": str, "link": str, "source": str}}
        source_counter = 1
        
        # Задачи Jira
        if grouped.get("jira"):
            parts.append("📌 ЗАДАЧИ JIRA:")
            for r in grouped["jira"][:5]:
                text = r['text'][:300]
                key = r.get('metadata', {}).get('key', '')
                link = r.get('link', '') or r.get('metadata', {}).get('link', '')
                
                # Сохраняем информацию об источнике
                sources[source_counter] = {
                    "title": key or r.get('title', text[:50]),
                    "link": link,
                    "source": "jira"
                }
                
                parts.append(f"[{source_counter}] {text}")
                source_counter += 1
            parts.append("")
        
        # События календаря
        if grouped.get("google_calendar"):
            parts.append("📅 СОБЫТИЯ:")
            for r in grouped["google_calendar"][:5]:
                text = r['text'][:300]
                link = r.get('link', '')
                title = r.get('metadata', {}).get('title', text[:50])
                
                sources[source_counter] = {
                    "title": title,
                    "link": link,
                    "source": "calendar"
                }
                
                parts.append(f"[{source_counter}] {text}")
                source_counter += 1
            parts.append("")
        
        # Сообщения Telegram
        if grouped.get("telegram"):
            parts.append("💬 СООБЩЕНИЯ:")
            for r in grouped["telegram"][:5]:
                text = r['text'][:300]
                chat = r.get('metadata', {}).get('chat', 'чат')
                link = r.get('link', '')
                
                sources[source_counter] = {
                    "title": f"Сообщение из {chat}",
                    "link": link,
                    "source": "telegram"
                }
                
                parts.append(f"[{source_counter}] {text}")
                source_counter += 1
            parts.append("")
        
        # Fallback
        if not parts:
            for i, r in enumerate(results[:5], 1):
                text = r['text'][:300]
                parts.append(f"[{i}] {text}")
                sources[i] = {
                    "title": text[:50],
                    "link": r.get('link', ''),
                    "source": "unknown"
                }
        
        context_text = "\n".join(parts)
        return context_text, sources


class RAGPipeline:

    def __init__(self, retriever):
        self.retriever = retriever
        self.context_engine = ContextEngine()

    def run(self, query: str, top_k: int = 5):

        results = self.retriever.retrieve(query, limit=top_k)

        context = self.context_engine.build(query, results)

        return {
            "context": context,
            "results": results
        }
    

# Основные возможности:
# 1. Гибридный поиск: комбинация плотного (векторного) и разреженного (BM25) поиска
# 2. Объединение результатов через Reciprocal Rank Fusion (RRF)
# 3. Формирование структурированного контекста с приоритизацией источников
# 4. Интеграция с векторным хранилищем (Chroma) и BM25 индексом
#
# Классы и их назначение:
#
# 1. RAGPipeline:
#    - Главный оркестратор RAG процесса
#    - Принимает запрос, вызывает ретривер, строит контекст
#    - Возвращает контекст и сырые результаты поиска
#
# 2. HybridRetriever:
#    - Комбинирует результаты из двух поисковых систем
#    - Векторный поиск: ищет сообщения и задачи по семантике
#    - BM25 поиск: ищет по ключевым словам
#    - Использует Reciprocal Rank Fusion для объединения результатов
#
# 3. ContextEngine:
#    - Преобразует сырые результаты поиска в структурированный контекст
#    - Группирует результаты по источникам (Jira, Google Calendar, Telegram)
#    - Сортирует по приоритету: задачи → события → сообщения
#    - Форматирует с эмодзи для визуального выделения

# Приоритеты контекста (от высшего к низшему):
# 1. 📌 TASKS — задачи из Jira (критичная информация)
# 2. 📅 EVENTS — события из календаря
# 3. 💬 MESSAGES — сообщения из Telegram