from google import genai
from google.genai import types
from 
import config


client = genai.Client(api_key=config.GEMINI_API_KEY)



def rag_with_gemini(query: str, top_k: int = 5) -> str:
    """
    RAG pipeline с Google Gemini.

    Args:
        query: Поисковый запрос пользователя
        top_k: Количество релевантных фрагментов контекста

    Returns:
        Ответ Gemini на основе контекста
    """

    MODEL_NAME = "gemini-2.5-flash-lite"

    result = rag_pipeline(query, top_k=top_k, verbose=False)
    context = result['context']

    prompt = f"""Контекст из корпоративных коммуникаций:
    {context}

    Вопрос пользователя: {query}

    Ответь на вопрос, используя только информацию из контекста.
    Если в контексте нет нужной информации, так и скажи.
    """

    response = client.models.generate_content(
    model=MODEL_NAME,
    config=types.GenerateContentConfig(
        system_instruction=config.RAG_SYSTEM_PROMPT,
        temperature=0,
        top_p=0.95,
        max_output_tokens=1000),
        contents=prompt
    )


    return response.text