import os
from dotenv import load_dotenv
import json

load_dotenv()

class Config:

    # Telegram
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    API_HASH = os.getenv("API_HASH")
    API_ID = int(os.getenv("API_ID", "0"))
    
    # Jira
    JIRA_URL = os.getenv("JIRA_URL")
    JIRA_EMAIL = os.getenv("JIRA_EMAIL")
    JIRA_TOKEN = os.getenv("JIRA_TOKEN")
    JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")
    
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # RAG
    RAG_PERSIST_DIR = os.getenv("RAG_PERSIST_DIR", "./data/chroma")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")

    jira_mapping_str = os.getenv("JIRA_USER_MAPPING", "{}")
    try:
        JIRA_USER_MAPPING = json.loads(jira_mapping_str)
    except json.JSONDecodeError:
        JIRA_USER_MAPPING = {}
    JIRA_ASSIGNER = os.getenv("JIRA_ASSIGNER")

    GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    GOOGLE_TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "token.pickle")

    TELEGRAM_CHATS_TO_READ = os.getenv("TELEGRAM_CHATS_TO_READ", "").split(",")


    @classmethod
    def get_jira_user(cls, telegram_user_id: str) -> str:
        """Возвращает Jira username по Telegram ID"""
        return cls.JIRA_USER_MAPPING.get(telegram_user_id, "")
    
    HF_TOKEN = os.getenv('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')

    RAG_SYSTEM_PROMPT = """
    Ты — планировщик и твоя задача чётко структурировать задачи и понимать их временной контекст. Отвечай на вопросы сотрудников,
    опираясь ТОЛЬКО на предоставленный контекст. Если ответа нет в контексте — честно скажи
    "Я не нашёл информацию по этому вопросу в базе знаний".
    В конце ответа обязательно укажи источники.
    """