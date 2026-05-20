import os
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import hashlib
import logging
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, persist_dir: str = Config.RAG_PERSIST_DIR, model_name: str = Config.EMBEDDING_MODEL):
        self.persist_dir = persist_dir
        
        # Инициализируем модель напрямую для ручного контроля префиксов E5
        self.model = SentenceTransformer(model_name)
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        # Инициализируем коллекции без передачи embedding_function в Chroma, 
        # так как мы будем передавать готовые векторы самостоятельно
        self.messages_collection = self.client.get_or_create_collection(
            name="messages",
            metadata={"hnsw:space": "cosine"}
        )
        self.tasks_collection = self.client.get_or_create_collection(
            name="tasks",
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info("Vector store initialized with manual E5 embeddings")
    
    def _generate_id(self, source: str, source_id: str) -> str:
        content = f"{source}_{source_id}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def add_document(self, doc: Dict) -> bool:
        try:
            doc_id = doc.get("id")
            if not doc_id:
                doc_id = self._generate_id(
                    doc.get("source", "unknown"),
                    doc.get("source_id", "")
                )
            
            text = doc.get("text", "")[:1000]
            doc_type = doc.get("type", "message")
            collection = self.messages_collection if doc_type == "message" else self.tasks_collection
            
            metadata = {
                "source": doc.get("source", "unknown"),
                "type": doc_type,
                "timestamp": doc.get("timestamp", ""),
                "link": doc.get("link", ""),
            }
            if "metadata" in doc and doc["metadata"]:
                for key, value in doc["metadata"].items():
                    if isinstance(value, (str, int, float, bool)):
                        metadata[key] = value
            
            # Добавляем префикс "passage: " перед генерацией вектора для E5
            embedding = self.model.encode(f"passage: {text}", normalize_embeddings=True).tolist()
            
            collection.upsert(
                ids=[doc_id], 
                documents=[text], 
                embeddings=[embedding], 
                metadatas=[metadata]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False
    
    def search_messages(self, query: str, source: str = None, limit: int = 5) -> List[Dict]:
        try:
            where_filter = {"source": source} if source else None
            # Добавляем префикс "query: " перед поиском для E5
            query_embedding = self.model.encode(f"query: {query}", normalize_embeddings=True).tolist()
            
            results = self.messages_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_filter
            )
            
            formatted = []
            if results and results.get('ids') and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    formatted.append({
                        'id': doc_id,
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results.get('distances') else None
                    })
            return formatted
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def search_similar_tasks(self, query: str, limit: int = 5) -> List[Dict]:
        try:
            # Добавляем префикс "query: " перед поиском для E5
            query_embedding = self.model.encode(f"query: {query}", normalize_embeddings=True).tolist()
            
            results = self.tasks_collection.query(
                query_embeddings=[query_embedding], 
                n_results=limit
            )
            formatted = []
            if results and results.get('ids') and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    formatted.append({
                        'id': doc_id,
                        'key': results['metadatas'][0][i].get('key', ''),
                        # НЕ обрезаем текст здесь, чтобы не ломать сопоставление в RRF фьюжн
                        'text': results['documents'][0][i], 
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if results.get('distances') else None
                    })
            return formatted
        except Exception as e:
            logger.error(f"Task search failed: {e}")
            return []
    
    def count_messages(self) -> int:
        try:
            return self.messages_collection.count()
        except:
            return 0
# Класс VectorStore:

# Инициализация:
# - Создаёт директорию для персистентного хранения ChromaDB
# - Загружает SentenceTransformer модель e5-small (384 измерения)
# - Создаёт или открывает коллекции: "messages" и "tasks"
# - Настраивает кастомную функцию эмбеддинга с префиксами E5

# Ключевые методы:
#
# 1. search_messages(query, source, limit):
#    - Поиск сообщений по семантическому запросу
#    - Добавляет префикс "query: " для e5 модели
#    - Поддерживает фильтрацию по источнику (telegram, и т.д.)
#    - Возвращает список с id, text, metadata, distance
#
# 2. search_similar_tasks(query, limit):
#    - Поиск похожих задач Jira
#    - Использует коллекцию tasks
#    - Возвращает результат с ключами, текстом и метаданными
#
# 3. add_message(message) / add_task(task):
#    - Добавление одного сообщения или задачи в коллекцию
#    - Генерирует уникальный ID через MD5(source + source_id)
#    - Для e5 добавляет префикс "passage: " при индексации
#    - Текст обрезается до 1000 символов
#
# 4. add_messages_batch(messages):
#    - Пакетное добавление сообщений
#    - Возвращает количество успешно добавленных
#
# 5. add_document(doc):
#    - Универсальный метод добавления документа
#    - Автоматически определяет коллекцию по doc["type"]
#
# 6. get_relevant_context(query, user_context, limit):
#    - Поиск релевантного контекста для RAG
#    - Форматирует результат в структурированный текст
#
# 7. count_messages() / clear_all():
#    - Счётчик сообщений и очистка всех коллекций

# Технические особенности:
#
# 1. E5 Embedding Model (intfloat/multilingual-e5-small):
#    - Мультиязычная модель (поддерживает 100+ языков)
#    - Размерность: 384 вектора
#    - Требует префиксы: "query: " для поиска, "passage: " для индексации
#    - Нормализация эмбеддингов (cosine similarity)
#
# 2. Кастомная функция эмбеддинга:
#    - Автоматически добавляет префикс "passage: " для индексируемых текстов
#    - ChromaDB вызывает её при вставке документов
#    - Для поиска префикс добавляется явно в методе search
#
# 3. Генерация ID:
#    - Формула: MD5(f"{source}_{source_id}")
#    - Обеспечивает детерминированные ID для дедупликации
#    - Позволяет обновлять существующие документы через upsert
#
# 4. Структура коллекций:
#    - messages: сообщения из Telegram, Google Calendar
#    - tasks: задачи из Jira
#    - Раздельное хранение улучшает качество поиска

# Формат метаданных:
# - source: источник (telegram, jira, google_calendar)
# - source_id: оригинальный ID из источника
# - timestamp: временная метка
# - link: ссылка на оригинал
# - дополнительные поля из metadata (статус, приоритет и т.д.)



# ВАЖНЫЕ ЗАМЕЧАНИЯ:
#
# 1. ПРЕФИКСЫ E5:
#    - Очень важно правильно добавлять префиксы
#    - Без префикса "passage:" качество индексации упадёт
#    - Без префикса "query:" поиск будет некорректным
#
# 2. ОБРЕЗКА ТЕКСТА:
#    - Текст ограничен 1000 символами
#    - Длинные сообщения теряют контекст
#    - Для Telegram это может быть проблемой

# 3. ID ГЕНЕРАЦИЯ:
#    - MD5 даёт 32 символа, но возможны коллизии при разных source_id
#    - Не использует timestamp, поэтому обновление документа перезаписывает старый

# 4. ПРОИЗВОДИТЕЛЬНОСТЬ:
#    - add_messages_batch делает отдельную вставку для каждого сообщения
#    - Нет пакетной вставки через collection.add()
#    - При 1000+ сообщениях будет медленно

# Использование:
# vs = VectorStore(persist_dir="./data/chroma")
# vs.add_message(message_dict)
# results = vs.search_messages("что планируется на сегодня?", limit=5)