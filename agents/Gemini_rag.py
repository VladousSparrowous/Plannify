"""RAG пайплайн с интеграцией Gemini"""
from google import genai
from google.genai import types
from config import Config

from storage.vector_store import VectorStore
from storage.bm25_store import BM25Store
from rag.hybrid_retriever import HybridRetriever
from rag.hybrid_retriever import RAGPipeline

# Глобальные экземпляры (инициализируются один раз)
_vector_store = None
_bm25_store = None
_retriever = None
_pipeline = None


def _init_rag():
    """Ленивая инициализация RAG компонентов"""
    global _vector_store, _bm25_store, _retriever, _pipeline
    
    if _pipeline is not None:
        return
    
    _vector_store = VectorStore(persist_dir=Config.RAG_PERSIST_DIR)
    _bm25_store = BM25Store()
    _retriever = HybridRetriever(_vector_store, _bm25_store)
    _pipeline = RAGPipeline(_retriever)


def rag_pipeline(query: str, top_k: int = 5, verbose: bool = False) -> dict:
    """
    Основной RAG пайплайн для поиска и формирования контекста.
    
    Args:
        query: Поисковый запрос
        top_k: Количество релевантных фрагментов
        verbose: Логировать ли результаты
    
    Returns:
        Словарь с ключом 'context' — строка с объединёнными фрагментами
    """
    _init_rag()
    
    result = _pipeline.run(query, top_k=top_k)
    
    if verbose:
        print(f"Query: {query}")
        print(f"Context length: {len(result['context'])} chars")
        print(f"Results count: {len(result['results'])}")
    
    return result


def rag_with_gemini(query: str, top_k: int = 5) -> str:
    """
    RAG pipeline с Google Gemini.
    
    Args:
        query: Поисковый запрос пользователя
        top_k: Количество релевантных фрагментов контекста
    
    Returns:
        Ответ Gemini на основе контекста
    """
    _init_rag()
    
    MODEL_NAME = "gemini-2.5-flash-lite"
    
    # Получаем контекст через RAG пайплайн
    result = rag_pipeline(query, top_k=top_k, verbose=False)
    context = result['context']
    
    prompt = f"""Контекст из корпоративных коммуникаций:
{context}

Вопрос пользователя: {query}

Ответь на вопрос, используя только информацию из контекста.
Если в контексте нет нужной информации, так и скажи.
"""
    
    client = genai.Client(api_key=Config.GEMINI_API_KEY)
    response = client.models.generate_content(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(
            system_instruction=Config.RAG_SYSTEM_PROMPT,
            temperature=0,
            top_p=0.95,
            max_output_tokens=1000
        ),
        contents=prompt
    )
    
    return response.text