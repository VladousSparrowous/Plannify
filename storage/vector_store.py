# storage/vector_store.py
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import hashlib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStore:

    
    def __init__(self, persist_dir: str = "./data/chroma", model_name: str = "intfloat/multilingual-e5-small"):
        """
        Args:
            persist_dir: Директория для хранения данных ChromaDB
            model_name: Мультиязычная модель e5 для русского и английского
        """
        self.persist_dir = persist_dir
        self.model_name = model_name

        try:
            # Для e5 модели нужно добавлять префикс "query: " при поиске
            # и "passage: " при индексации, но SentenceTransformer это делает автоматически
            self.model = SentenceTransformer(model_name)
            logger.info(f"✅ Loaded multilingual model: {model_name}")
            logger.info(f"   Model dimensions: {self.model.get_embedding_dimension()}")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            logger.info("   Попробуйте: uv add sentence-transformers")
            raise
        
        # Создаём функцию эмбеддинга для ChromaDB
        self.embedding_fn = self._create_embedding_function()
        
        # Инициализируем ChromaDB клиент
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        # Создаём или получаем коллекции
        self.messages_collection = self.client.get_or_create_collection(
            name="messages",
            embedding_function=self.embedding_fn
        )
        
        self.tasks_collection = self.client.get_or_create_collection(
            name="tasks",
            embedding_function=self.embedding_fn
        )
        
        logger.info("✅ Vector store initialized with multilingual-e5-small")
    
    def _create_embedding_function(self):
        """Создаёт функцию эмбеддинга для ChromaDB с правильным префиксом e5"""
        
        class E5EmbeddingFunction:
            def __init__(self, model):
                self.model = model
            
            def __call__(self, texts):
                # Для e5 модели: добавляем префикс "passage: " для индексации
                # ChromaDB вызывает эту функцию для вставляемых текстов
                prefixed_texts = [f"passage: {text}" for text in texts]
                return self.model.encode(prefixed_texts, normalize_embeddings=True).tolist()
        
        return E5EmbeddingFunction(self.model)
    
    def search_messages(self, query: str, source: str = None, limit: int = 5) -> List[Dict]:
        """
        Поиск похожих сообщений с правильным префиксом для e5
        """
        try:
            # Для поиска используем префикс "query: "
            search_query = f"query: {query}"
            
            where_filter = {"source": source} if source else None
            
            results = self.messages_collection.query(
                query_texts=[search_query],
                n_results=limit,
                where=where_filter
            )
            
            formatted_results = []
            if results and results.get('ids') and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    formatted_results.append({
                        'id': doc_id,
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if results.get('distances') else None
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def _generate_id(self, source: str, source_id: str) -> str:
        content = f"{source}_{source_id}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def add_message(self, message: Dict) -> bool:
        try:
            doc_id = self._generate_id(
                message.get('source', 'unknown'),
                message.get('source_id', '')
            )
            
            # Для e5 модели текст должен быть коротким и чистым
            text = message.get('text', '')[:1000]
            
            self.messages_collection.upsert(
                ids=[doc_id],
                documents=[text],
                metadatas=[{
                    'source': message.get('source', ''),
                    'source_id': message.get('source_id', ''),
                    'timestamp': message.get('timestamp', ''),
                    'link': message.get('link', ''),
                    **message.get('metadata', {})
                }]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            return False
    
    def add_messages_batch(self, messages: List[Dict]) -> int:
        success_count = 0
        for message in messages:
            if self.add_message(message):
                success_count += 1
        logger.info(f"Added {success_count}/{len(messages)} messages")
        return success_count
    
    def add_task(self, task: Dict) -> bool:
        try:
            doc_id = self._generate_id('jira', task.get('source_id', ''))
            
            text = f"{task.get('title', '')}\n{task.get('text', '')}"[:1000]
            
            self.tasks_collection.upsert(
                ids=[doc_id],
                documents=[text],
                metadatas={
                    'key': task.get('source_id', ''),
                    'status': task.get('metadata', {}).get('status', ''),
                    'priority': task.get('metadata', {}).get('priority', ''),
                    'link': task.get('link', '')
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add task: {e}")
            return False
        
    def add_document(self, doc: Dict) -> bool:
        """
        Универсальный метод вставки документа
        """
        try:
            doc_id = doc["id"]
            text = doc["text"][:1000]

            collection = (
                self.messages_collection
                if doc["type"] == "message"
                else self.tasks_collection
            )

            collection.upsert(
                ids=[doc_id],
                documents=[text],
                metadatas=[{
                    "source": doc.get("source"),
                    "type": doc.get("type"),
                    "timestamp": doc.get("timestamp"),
                    **doc.get("metadata", {})
                }]
            )

            return True

        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False    
    

    def search_similar_tasks(self, query: str, limit: int = 5) -> List[Dict]:
        try:
            search_query = f"query: {query}"
            
            results = self.tasks_collection.query(
                query_texts=[search_query],
                n_results=limit
            )
            
            formatted_results = []
            if results and results.get('ids') and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    formatted_results.append({
                        'key': results['metadatas'][0][i].get('key', ''),
                        'text': results['documents'][0][i][:100],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if results.get('distances') else None
                    })
            return formatted_results
        except Exception as e:
            logger.error(f"Task search failed: {e}")
            return []
    
    def get_relevant_context(self, query: str, user_context: str = None, limit: int = 3) -> str:
        results = self.search_messages(query, limit=limit)
        
        if not results:
            return ""
        
        context_parts = []
        for i, result in enumerate(results, 1):
            text = result.get('text', '')
            metadata = result.get('metadata', {})
            source = metadata.get('source', 'unknown')
            
            if text:
                context_parts.append(f"[{i}] [{source}] {text[:200]}")
        
        return "\n".join(context_parts)
    
    def count_messages(self) -> int:
        try:
            return self.messages_collection.count()
        except:
            return 0
    
    def clear_all(self) -> bool:
        try:
            self.client.delete_collection("messages")
            self.messages_collection = self.client.create_collection(
                name="messages",
                embedding_function=self.embedding_fn
            )
            self.client.delete_collection("tasks")
            self.tasks_collection = self.client.create_collection(
                name="tasks",
                embedding_function=self.embedding_fn
            )
            logger.info("Cleared all collections")
            return True
        except Exception as e:
            logger.error(f"Failed to clear: {e}")
            return False