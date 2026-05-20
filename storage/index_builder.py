from typing import List, Dict, Optional
from storage.vector_store import VectorStore
from storage.bm25_store import Document, Normalizer


class DocumentBuilder:
    """Преобразует сырые данные из коннекторов в формат Document"""
    
    @staticmethod
    def build_batch(source: str, items: List[Dict]) -> List[Document]:
        documents = []
        for item in items:
            doc = DocumentBuilder._build_single(source, item)
            if doc:
                documents.append(doc)
        return documents
    
    @staticmethod
    def _build_single(source: str, item: Dict) -> Optional[Document]:
        if source == 'telegram':
            return {
                "id": item.get("id", f"tg_{item.get('source_id', '')}"),
                "text": item.get("text", ""),
                "type": "message",
                "source": "telegram",
                "timestamp": item.get("timestamp"),
                "link": item.get("link"),
                "metadata": item.get("metadata", {})
            }
        
        elif source == 'jira':
            # Добавляем больше контекста для поиска
            metadata = item.get('metadata', {})
            enhanced_text = f"""
                Задача: {item.get('title', '')}
                Ключ: {item.get('source_id', '')}
                Статус: {metadata.get('status', '')}
                Приоритет: {metadata.get('priority', '')}
                Описание: {item.get('text', '')}
                """
            return {
                "id": item.get("source_id", ""),
                "text": enhanced_text,  # ← более богатый текст
                "type": "task",
                "source": "jira",
                "timestamp": item.get("timestamp"),
                "link": item.get("link"),
                "metadata": metadata
                }
                
        elif source == 'calendar':
            return {
                "id": item.get("source_id", ""),
                "text": f"{item.get('title', '')}: {item.get('text', '')}",
                "type": "event",
                "source": "google_calendar",
                "timestamp": item.get("timestamp"),
                "link": item.get("link"),
                "metadata": item.get("metadata", {})
            }
        
        return None


class IndexBuilder:
    def __init__(self, vector_store: VectorStore):
        self.vs = vector_store

    def rebuild_all(self, sources: dict) -> List[Document]:
        """
        sources = {
            "telegram": [...],
            "jira": [...],
            "calendar": [...]
        }
        """
        all_docs = []
        
        for source, items in sources.items():
            docs = DocumentBuilder.build_batch(source, items)
            all_docs.extend(docs)
            
            for doc in docs:
                normalized = Normalizer.enforce(doc)
                self.vs.add_document(normalized)
        
        return all_docs