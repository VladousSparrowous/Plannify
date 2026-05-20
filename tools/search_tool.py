from connectors.telegram_reader import TelegramReaderConnector
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class SearchTool:
    """
    Инструмент для поиска по истории чатов
    """
    
    def __init__(self, telegram_reader: TelegramReaderConnector):
        self.telegram = telegram_reader
    
    async def search_in_chats(
        self, 
        query: str, 
        chat_ids: List[str],
        since_days: int = 7
    ) -> List[Dict]:
        """
        Поиск по всем указанным чатам
        
        Args:
            query: Поисковый запрос
            chat_ids: Список ID чатов для поиска
            since_days: За сколько дней искать
        """
        from datetime import datetime, timedelta
        since = datetime.now() - timedelta(days=since_days)
        
        all_results = []
        for chat_id in chat_ids:
            results = await self.telegram.search_in_chat(
                chat_id=chat_id,
                query=query,
                since=since,
                limit=10
            )
            all_results.extend(results)
        
        # Сортируем по времени (новые сверху)
        all_results.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return all_results
    
    def format_search_response(self, results: List[Dict], query: str) -> str:
        """Форматирует результаты поиска для отправки в Telegram"""
        if not results:
            return f"🔍 Ничего не найдено по запросу: {query}"
        
        response = f"🔍 **Результаты поиска:** «{query}»\n\n"
        
        for i, result in enumerate(results[:10], 1):
            # Обрезаем длинные сообщения
            text = result['text'][:100] + '...' if len(result['text']) > 100 else result['text']
            chat_title = result['metadata'].get('chat_title', 'чат')
            
            response += (
                f"{i}. **{chat_title}**\n"
                f"   {text}\n"
                f"   🔗 [Открыть в Telegram]({result['link']})\n\n"
            )
        
        return response