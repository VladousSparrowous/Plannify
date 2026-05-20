from connectors.jira import JiraConnector
from typing import List, Dict
import logging

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
        Форматирует список задач для отправки в Telegram
        
        Возвращает Markdown с ссылками на задачи
        """
        if not tasks:
            return "✅ У вас нет активных задач в Jira."
        
        response = "🐞 **Ваши задачи в Jira:**\n\n"
        
        for task in tasks:
            metadata = task['metadata']
            response += (
                f"{metadata['priority_emoji']} **{task['source_id']}** — {task['title'][:60]}\n"
                f"   📊 Статус: {metadata['status']}\n"
                f"   👤 Назначено: {metadata['assignee']}\n"
                f"   🔗 [Открыть в Jira]({task['link']})\n\n"
            )
        
        response += f"📋 Всего: {len(tasks)} задач"
        return response