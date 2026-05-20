import os
from dotenv import load_dotenv

load_dotenv()

class Config:

    # Telegram
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    # Jira
    JIRA_URL = os.getenv("JIRA_URL")
    JIRA_EMAIL = os.getenv("JIRA_EMAIL")
    JIRA_TOKEN = os.getenv("JIRA_TOKEN")
    JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")
    
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # RAG
    RAG_PERSIST_DIR = os.getenv("RAG_PERSIST_DIR", "./data/chroma")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")

    JIRA_USER_MAPPING = {
        # "telegram_user_id": "jira_username"
        "123456789": "ivan.petrov",
    }

    GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    GOOGLE_TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "token.pickle")

    TELEGRAM_CHATS_TO_READ = os.getenv("TELEGRAM_CHATS_TO_READ", "").split(",")


    RAG_SYSTEM_PROMPT="""
    Ты — планировщик и твоя задача чётко структурировать задачи и понимать их временной контекст. Отвечай на вопросы сотрудников,
    опираясь ТОЛЬКО на предоставленный контекст. Если ответа нет в контексте — честно скажи
    "Я не нашёл информацию по этому вопросу в базе знаний".
    В конце ответа обязательно укажи источники в формате [N].
    """