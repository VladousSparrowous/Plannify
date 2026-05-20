
import asyncio
import logging
from datetime import datetime

from config import Config
from connectors.telegram_history import TelegramConnector
from connectors.jira import JiraConnector
from connectors.google_calendar import GoogleCalendarConnector
from storage.vector_store import VectorStore
from storage.bm25_store import BM25Store, Normalizer
from storage.index_builder import IndexBuilder, DocumentBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fetch_telegram_messages(connector: TelegramConnector, chats: list) -> list:
    """Загружает сообщения из Telegram чатов"""
    all_messages = []
    for chat in chats:
        if not chat:
            continue
        try:
            messages = await connector.get_messages(chat, limit=200)
            logger.info(f" {chat}: {len(messages)} messages")
            all_messages.extend(messages)
        except Exception as e:
            logger.error(f"Failed to fetch {chat}: {e}")
    return all_messages


def fetch_jira_tasks(connector: JiraConnector) -> list:
    """Загружает задачи из Jira"""
    try:
        tasks = connector.get_my_tasks(assignee=Config.JIRA_ASSIGNER, limit=100)
        logger.info(f"  📋 Jira: {len(tasks)} tasks")
        return tasks
    except Exception as e:
        logger.error(f"Failed to fetch Jira tasks: {e}")
        return []


def fetch_calendar_events(connector: GoogleCalendarConnector) -> list:
    """Загружает события из Google Calendar"""
    try:
        events = connector.get_week_events()
        logger.info(f"  📅 Calendar: {len(events)} events")
        return events
    except Exception as e:
        logger.error(f"Failed to fetch calendar events: {e}")
        return []


async def main():
    logger.info("🚀 Starting data indexing...")
    
    # 1. Инициализация хранилищ
    vector_store = VectorStore(persist_dir=Config.RAG_PERSIST_DIR)
    bm25_store = BM25Store()
    
    # 2. Загрузка данных из источников
    sources_data = {}
    
    # Telegram
    if Config.TELEGRAM_TOKEN and Config.API_HASH:
        logger.warning("Telegram connector requires API_ID and API_HASH in Config")
        Telegram_Connector = TelegramConnector(Config.TELEGRAM_TOKEN, Config.API_HASH)
        sources_data["telegram"] = await fetch_telegram_messages(Telegram_Connector, Config.TELEGRAM_CHATS_TO_READ)
    else:
        sources_data["telegram"] = []
    
    # Jira
    if Config.JIRA_TOKEN:
        jira_connector = JiraConnector(
            url=Config.JIRA_URL,
            email=Config.JIRA_EMAIL,
            token=Config.JIRA_TOKEN,
            project_key=Config.JIRA_PROJECT_KEY,
        )
        sources_data["jira"] = fetch_jira_tasks(jira_connector)
    else:
        sources_data["jira"] = []
    
    # Calendar
    if Config.GOOGLE_CREDENTIALS_PATH:
        try:
            calendar_connector = GoogleCalendarConnector(
                credentials_path=Config.GOOGLE_CREDENTIALS_PATH,
                token_path=Config.GOOGLE_TOKEN_PATH,
            )
            sources_data["calendar"] = fetch_calendar_events(calendar_connector)
        except Exception as e:
            logger.error(f"Calendar connector failed: {e}")
            sources_data["calendar"] = []
    else:
        sources_data["calendar"] = []
    
    # 3. Построение индексов
    builder = IndexBuilder(vector_store)
    documents = builder.rebuild_all(sources_data)
    
    logger.info(f"📄 Total normalized documents: {len(documents)}")
    
    # 4. Построение BM25 индекса
    bm25_docs = [
        {"text": d["text"], "metadata": d["metadata"]}
        for d in documents
    ]
    bm25_store.rebuild(bm25_docs)
    
    logger.info("✅ Indexing complete!")
    logger.info(f"   Messages in Chroma: {vector_store.count_messages()}")
    logger.info(f"   BM25 documents: {len(bm25_store.docs)}")


if __name__ == "__main__":
    asyncio.run(main())