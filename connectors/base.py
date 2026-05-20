from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

@dataclass
class Message:
    """Универсальный формат сообщения из любого источника"""
    source: str           # 'telegram', 'slack', 'email', 'jira', 'google_calendar'
    source_id: str        # ID чата, канала, отправителя
    text: str             # Текст сообщения
    timestamp: datetime   # Время отправки
    thread_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class BaseConnector(ABC):
    """Абстрактный класс для всех коннекторов"""
    
    @abstractmethod
    async def fetch_new(self, since: datetime) -> list['Message']:
        """Получить новые сообщения с указанного времени"""
        pass
    
    @abstractmethod
    async def validate(self) -> bool:
        """Проверить валидность подключения"""
        pass