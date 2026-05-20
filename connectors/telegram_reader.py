from telegram import Bot
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramReaderConnector:
    """
    Коннектор для чтения сообщений из Telegram чатов/каналов
    """
    
    def __init__(self, token: str):
        """
        Args:
            token: Telegram Bot токен
        """
        self.token = token
        
        # Настройка прокси для бота
       
        self.bot = Bot(token=token)
        logger.info("✅ Telegram reader initialized (no proxy)")
    
    async def get_chat_messages(
        self, 
        chat_id: str, 
        limit: int = 50,
        since: datetime = None
    ) -> List[Dict]:
        """
        Получить сообщения из чата/канала
        
        Args:
            chat_id: ID чата (например, -1001234567890 для канала)
            limit: Максимум сообщений
            since: Начиная с даты (опционально)
        
        Returns:
            Список сообщений в унифицированном формате
        """
        try:
            messages = []
            
            # Для каналов и супергрупп
            if since:
                # Преобразуем datetime в timestamp
                since_ts = int(since.timestamp())
            else:
                since_ts = None
            
            # Получаем историю сообщений
            # Используем get_updates или специальные методы для каналов
            updates = await self.bot.get_updates(
                allowed_updates=['message', 'channel_post'],
                timeout=30
            )
            
            for update in updates:
                # Проверяем, есть ли сообщение в нужном чате
                message = update.message or update.channel_post
                if not message:
                    continue
                
                # Фильтруем по chat_id
                if str(message.chat_id) != str(chat_id):
                    continue
                
                # Фильтруем по дате
                if since_ts and message.date.timestamp() < since_ts:
                    continue
                
                formatted = self._format_message(message)
                if formatted:
                    messages.append(formatted)
                    
                    if len(messages) >= limit:
                        break
            
            logger.info(f"📨 Got {len(messages)} messages from chat {chat_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get messages from {chat_id}: {e}")
            return []
    
    async def search_in_chat(
        self, 
        chat_id: str, 
        query: str, 
        limit: int = 20,
        since: datetime = None
    ) -> List[Dict]:
        """
        Поиск сообщений по тексту в чате
        
        Args:
            chat_id: ID чата
            query: Поисковый запрос
            limit: Максимум результатов
            since: Начиная с даты
        """
        try:
            all_messages = await self.get_chat_messages(chat_id, limit=100, since=since)
            
            # Простой текстовый поиск
            query_lower = query.lower()
            matched = []
            
            for msg in all_messages:
                if query_lower in msg.get('text', '').lower():
                    matched.append(msg)
                    if len(matched) >= limit:
                        break
            
            logger.info(f"🔍 Found {len(matched)} messages matching '{query}'")
            return matched
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    async def get_mentions(
        self, 
        username: str, 
        chat_ids: List[str],
        since: datetime = None,
        limit: int = 30
    ) -> List[Dict]:
        """
        Получить упоминания пользователя в чатах
        
        Args:
            username: Имя пользователя (@username или ID)
            chat_ids: Список чатов для поиска
            since: Начиная с даты
            limit: Максимум результатов
        """
        try:
            mentions = []
            
            for chat_id in chat_ids:
                messages = await self.get_chat_messages(chat_id, limit=100, since=since)
                
                for msg in messages:
                    text = msg.get('text', '')
                    # Проверяем упоминания
                    if f"@{username}" in text or username in text:
                        mentions.append(msg)
                        if len(mentions) >= limit:
                            break
                
                if len(mentions) >= limit:
                    break
            
            logger.info(f"📢 Found {len(mentions)} mentions of {username}")
            return mentions
            
        except Exception as e:
            logger.error(f"Failed to get mentions: {e}")
            return []
    
    def _format_message(self, message) -> Optional[Dict]:
        """
        Приводит сообщение Telegram к унифицированному формату
        """
        try:
            # Определяем тип чата
            chat = message.chat
            chat_type = chat.type  # 'private', 'group', 'supergroup', 'channel'
            
            # Получаем текст сообщения
            text = message.text or message.caption or ''
            
            # Формируем ссылку на сообщение
            # Формат: https://t.me/c/chat_id/message_id
            chat_id = str(chat.id)
            # Для супергрупп нужно убрать -100 из ID
            if chat_id.startswith('-100'):
                chat_link_id = chat_id[4:]
            else:
                chat_link_id = chat_id
            
            message_link = f"https://t.me/c/{chat_link_id}/{message.message_id}"
            
            return {
                # Универсальные поля
                'source': 'telegram',
                'source_id': str(message.message_id),
                'title': f"Сообщение в {chat.title or 'чате'}",
                'text': text,
                'timestamp': message.date.isoformat(),
                'link': message_link,
                
                # Специфичные поля
                'metadata': {
                    'chat_id': chat_id,
                    'chat_title': chat.title,
                    'chat_type': chat_type,
                    'message_id': message.message_id,
                    'sender_id': message.from_user.id if message.from_user else None,
                    'sender_name': message.from_user.full_name if message.from_user else None,
                    'sender_username': message.from_user.username if message.from_user else None,
                    'reply_to': message.reply_to_message.message_id if message.reply_to_message else None,
                }
            }
        except Exception as e:
            logger.error(f"Failed to format message: {e}")
            return None
    
    async def validate(self) -> bool:
        """Проверить подключение к Telegram API"""
        try:
            me = await self.bot.get_me()
            logger.info(f"✅ Telegram reader validated (bot: @{me.username})")
            return True
        except Exception as e:
            logger.error(f"❌ Telegram reader validation failed: {e}")
            return False