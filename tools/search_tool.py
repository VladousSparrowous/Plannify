from connectors.telegram_history import TelegramConnector
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class SearchTool:
    """
    Инструмент для поиска по истории чатов
    """
    
    def __init__(self, telegram_reader: TelegramConnector):
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
            return f"Ничего не найдено по запросу: {query}"
        
        response = f"**Результаты поиска:** «{query}»\n\n"
        
        for i, result in enumerate(results[:10], 1):
            # Обрезаем длинные сообщения
            text = result['text'][:100] + '...' if len(result['text']) > 100 else result['text']
            chat_title = result['metadata'].get('chat_title', 'чат')
            
            response += (
                f"{i}. **{chat_title}**\n"
                f"   {text}\n"
                f"   [Открыть в Telegram]({result['link']})\n\n"
            )
        
        return response
    

# Класс SearchTool:
#
# Инициализация:
# - Принимает экземпляр TelegramConnector (для работы с историей чатов)
# - Сохраняет его для дальнейшего использования
#
# Ключевые методы:
#
# 1. search_in_chats(query, chat_ids, since_days):
#    - Выполняет поиск по всем указанным чатам
#    - query: поисковый запрос (текст для поиска)
#    - chat_ids: список ID чатов (например, ['@channel_name', '-1001234567890'])
#    - since_days: глубина поиска в днях (по умолчанию 7 дней)
#    - Возвращает список найденных сообщений, отсортированных по времени (новые сверху)
#
# 2. format_search_response(results, query):
#    - Форматирует результаты поиска для отправки в Telegram
#    - Ограничивает вывод 10 результатами
#    - Обрезает длинные сообщения до 100 символов
#    - Добавляет ссылки на оригинальные сообщения в Telegram
#    - Возвращает Markdown строку