from connectors.google_calendar import GoogleCalendarConnector
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class CalendarTool:
    """
    Инструмент для работы с Google Calendar в рамках агента
    """
    
    def __init__(self, connector: GoogleCalendarConnector):
        self.connector = connector
    
    async def get_today_events(self) -> List[Dict]:
        """Получить события на сегодня"""
        return self.connector.get_today_events()
    
    async def get_tomorrow_events(self) -> List[Dict]:
        """Получить события на завтра"""
        return self.connector.get_tomorrow_events()
    
    async def get_week_events(self) -> List[Dict]:
        """Получить события на неделю"""
        return self.connector.get_week_events()
    
    async def get_events_for_date(self, date_str: str) -> List[Dict]:
        """Получить события на конкретную дату"""
        from datetime import datetime
        try:
            date = datetime.fromisoformat(date_str)
            return self.connector.get_events(date=date)
        except:
            return []
    
    def format_events_response(self, events: List[Dict], date_label: str = "сегодня") -> str:
        """
        Форматирует список событий для отправки в Telegram
        
        Возвращает Markdown с ссылками на события
        """
        if not events:
            return f"📅 На {date_label} встреч не запланировано."
        
        response = f"📅 **Ваши встречи на {date_label}:**\n\n"
        
        for i, event in enumerate(events, 1):
            meta = event['metadata']
            
            if meta['is_all_day']:
                time_str = "🌞 Весь день"
            else:
                time_str = f"🕐 {meta['start_human']} — {meta['end_human']}"
            
            location_str = f"\n   📍 {meta['location']}" if meta['location'] else ""
            
            response += (
                f"{i}. **{event['title']}**\n"
                f"   {time_str}{location_str}\n"
                f"   🔗 [Открыть в календаре]({event['link']})\n\n"
            )
        
        return response