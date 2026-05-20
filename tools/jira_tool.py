from connectors.jira import JiraConnector
from typing import List, Dict
import logging
import html

logger = logging.getLogger(__name__)

class JiraTool:
    """
    Инструмент для работы с Jira в рамках агента.
    Умеет получать задачи и форматировать их для ответа пользователю.
    """
    
    def __init__(self, connector: JiraConnector):
        self.connector = connector
    
    async def get_my_tasks(self, jira_user: str) -> List[Dict]:
        """Получить активные задачи пользователя"""
        return self.connector.get_my_tasks(assignee=jira_user)
    
    async def get_recent_updates(self, hours: int = 24) -> List[Dict]:
        """Получить недавние обновления"""
        return self.connector.get_recent_updates(hours=hours)
    
    async def search(self, query: str) -> List[Dict]:
        """Поиск по задачам"""
        return self.connector.search_issues(query)
    
    def format_tasks_response(self, tasks: List[Dict]) -> str:
        """
        Форматирует список задач для отправки в Telegram с использованием HTML
        """
        if not tasks:
            return "У вас нет активных задач в Jira."
        
        # Используем HTML-теги вместо Markdown
        response = "<b>Ваши задачи в Jira:</b>\n\n"
        
        for task in tasks:
            metadata = task['metadata']
            
            # Экранируем спецсимволы, чтобы избежать ошибок парсинга HTML
            safe_title = html.escape(task['title'][:60])
            safe_status = html.escape(metadata['status'])
            safe_assignee = html.escape(metadata['assignee'])
            
            response += (
                f"{metadata['priority_emoji']} <b>{task['source_id']}</b> — {safe_title}\n"
                f"   Статус: {safe_status}\n"
                f"   Назначено: {safe_assignee}\n"
                f"   <a href=\"{task['link']}\">Открыть в Jira</a>\n\n"
            )
        
        response += f"Всего: {len(tasks)} задач"
        return response
    

# Класс JiraTool:
#
# Инициализация:
# - Принимает готовый экземпляр JiraConnector
# - Сохраняет его для дальнейшего использования
#
# Ключевые методы:
#
# 1. get_my_tasks(jira_user):
#    - Получает активные задачи конкретного пользователя
#    - jira_user: Jira username (например, 'ivan.ivanov')
#    - Возвращает только незакрытые задачи (status не Closed/Done/Resolved)
#    - Обёртка над connector.get_my_tasks(assignee=jira_user)
#
# 2. get_recent_updates(hours):
#    - Получает задачи, обновлённые за последние N часов
#    - По умолчанию: 24 часа
#    - Полезно для дайджеста изменений
#    - Обёртка над connector.get_recent_updates(hours=hours)
#
# 3. search(query):
#    - Выполняет полнотекстовый поиск по задачам
#    - Ищет в полях summary и description
#    - Обёртка над connector.search_issues(query)
#
# 4. format_tasks_response(tasks):
#    - Форматирует список задач в читаемый Markdown
#    - Добавляет эмодзи приоритета (из metadata['priority_emoji'])
#    - Включает ссылки на задачи в Jira
#    - Возвращает строку для отправки в Telegram