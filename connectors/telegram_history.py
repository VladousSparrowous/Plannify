from telethon import TelegramClient
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class TelegramHistoryConnector:

    def __init__(self, api_id: int, api_hash: str):
        self.client = TelegramClient("session", api_id, api_hash)

    async def connect(self):
        await self.client.start()
        logger.info("✅ Telegram history client connected")

    async def get_messages(self, chat: str, limit: int = 100) -> List[Dict]:
        messages = []

        async for msg in self.client.iter_messages(chat, limit=limit):

            if not msg.text:
                continue

            messages.append({
                "id": f"tg_{msg.id}",
                "text": msg.text,
                "type": "message",
                "source": "telegram",
                "timestamp": msg.date.isoformat(),
                "link": None,
                "metadata": {
                    "chat": chat,
                    "message_id": msg.id,
                    "sender_id": msg.sender_id
                }
            })

        return messages

    async def search(self, chat: str, query: str, limit: int = 50):
        results = []

        async for msg in self.client.iter_messages(chat, search=query, limit=limit):

            results.append({
                "id": f"tg_{msg.id}",
                "text": msg.text,
                "type": "message",
                "source": "telegram",
                "timestamp": msg.date.isoformat(),
                "link": None,
                "metadata": {
                    "chat": chat,
                    "message_id": msg.id
                }
            })

        return results