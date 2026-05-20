import os
import pickle
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleCalendarConnector:
    """Коннектор для Google Calendar"""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    
    def __init__(self, credentials_path: str, token_path: str = 'token.pickle', proxy_url: str = None):
        """
        Args:
            credentials_path: Путь к credentials.json
            token_path: Где хранить токен авторизации
            proxy_url: Прокси URL (опционально)
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.proxy_url = proxy_url
        self.service = self._authenticate()
    
    def _authenticate(self):
        """Аутентификация в Google Calendar API"""
        creds = None
        
        # Загружаем сохранённый токен
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # Если токен не валиден или его нет
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("✅ Token refreshed")
                except Exception as e:
                    logger.error(f"Failed to refresh token: {e}")
                    creds = None
            
            if not creds:
                # Запрашиваем авторизацию
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
                logger.info("✅ New credentials obtained")
            
            # Сохраняем токен
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        # Создаём сервис
        service = build('calendar', 'v3', credentials=creds)
        logger.info("✅ Google Calendar service initialized")
        return service
    
    def get_events(self, date: datetime = None, days_ahead: int = 1) -> List[Dict]:
        """
        Получить события на указанную дату
        
        Args:
            date: Дата (если None — сегодня)
            days_ahead: На сколько дней вперёд (по умолчанию 1)
        
        Returns:
            Список событий в унифицированном формате
        """
        if date is None:
            date = datetime.now()
        
        # Форматируем временные границы
        start_of_day = datetime(date.year, date.month, date.day, 0, 0, 0)
        end_of_day = start_of_day + timedelta(days=days_ahead)
        
        start_iso = start_of_day.isoformat() + 'Z'
        end_iso = end_of_day.isoformat() + 'Z'
        
        try:
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_iso,
                timeMax=end_iso,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            result = []
            for event in events:
                formatted = self._format_event(event)
                if formatted:
                    result.append(formatted)
            
            logger.info(f"📅 Found {len(result)} events for {date.strftime('%Y-%m-%d')}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to fetch events: {e}")
            return []
    
    def get_today_events(self) -> List[Dict]:
        """Получить события на сегодня"""
        return self.get_events(date=datetime.now(), days_ahead=1)
    
    def get_tomorrow_events(self) -> List[Dict]:
        """Получить события на завтра"""
        tomorrow = datetime.now() + timedelta(days=1)
        return self.get_events(date=tomorrow, days_ahead=1)
    
    def get_week_events(self) -> List[Dict]:
        """Получить события на текущую неделю"""
        return self.get_events(date=datetime.now(), days_ahead=7)
    
    def _format_event(self, event: dict) -> Optional[Dict]:
        """
        Приводит событие Google Calendar к унифицированному формату
        """
        try:
            start = event.get('start', {})
            end = event.get('end', {})
            
            # Определяем время начала
            if 'dateTime' in start:
                start_time = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(end['dateTime'].replace('Z', '+00:00'))
                is_all_day = False
            else:
                # Целодневное событие
                start_time = datetime.fromisoformat(start['date'])
                end_time = datetime.fromisoformat(end['date'])
                is_all_day = True
            
            # Ссылка на событие (можно открыть в Google Calendar)
            event_link = f"https://calendar.google.com/calendar/event?eid={event.get('id', '')}"
            
            return {
                # Универсальные поля
                'source': 'google_calendar',
                'source_id': event.get('id', ''),
                'title': event.get('summary', 'Без названия'),
                'text': event.get('description', ''),
                'timestamp': start_time.isoformat(),
                'link': event_link,
                
                # Специфичные поля
                'metadata': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'start_human': start_time.strftime('%H:%M'),
                    'end_human': end_time.strftime('%H:%M'),
                    'is_all_day': is_all_day,
                    'location': event.get('location', ''),
                    'attendees': [a.get('email') for a in event.get('attendees', [])],
                    'status': event.get('status', 'confirmed'),
                }
            }
        except Exception as e:
            logger.error(f"Failed to format event: {e}")
            return None
    
    def validate(self) -> bool:
        """Проверить подключение к Google Calendar"""
        try:
            events = self.get_today_events()
            logger.info("✅ Google Calendar validated")
            return True
        except Exception as e:
            logger.error(f"❌ Google Calendar validation failed: {e}")
            return False