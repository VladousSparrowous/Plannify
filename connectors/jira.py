from jira import JIRA
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JiraConnector:
    """Коннектор для работы с Jira"""
    
    def __init__(self, url: str, email: str, token: str, project_key: str):
        """
        Инициализация подключения к Jira
        
        Args:
            url:
            email: 
            token: 
            project_key: 
        """
        self.url = url
        self.project_key = project_key
        
        try:
            self.jira = JIRA(
                server=url,
                basic_auth=(email, token),
                max_retries=2,
                timeout=30
            )
            logger.info(f"Connected to Jira: {url}")
        except Exception as e:
            logger.error(f"Failed to connect to Jira: {e}")
            raise
    
    def get_my_tasks(self, assignee: str = None, limit: int = 20) -> List[Dict]:
        """
        Получить задачи, назначенные на пользователя
        
        Args:
            assignee: Jira username (если None - текущий пользователь)
            limit: Максимальное количество задач
        
        Returns:
            Список задач в унифицированном формате
        """
        try:
            # Формируем JQL запрос
            if assignee:
                jql = f'project = {self.project_key} AND assignee = "{assignee}" AND status not in (Closed, Done, Resolved)'
            else:
                jql = f'project = {self.project_key} AND assignee = currentUser() AND status not in (Closed, Done, Resolved)'
            
            logger.info(f"Executing JQL: {jql}")
            issues = self.jira.search_issues(jql, maxResults=limit)
            
            tasks = []
            for issue in issues:
                tasks.append(self._format_issue(issue))
            
            logger.info(f"Found {len(tasks)} active tasks")
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to fetch tasks: {e}")
            return []
    
    def get_recent_updates(self, hours: int = 24, limit: int = 30) -> List[Dict]:
        """
        Получить недавние обновления по задачам
        
        Args:
            hours: За сколько часов (по умолчанию 24)
            limit: Максимальное количество
        
        Returns:
            Список обновлённых задач
        """
        try:
            since = datetime.now() - timedelta(hours=hours)
            since_str = since.strftime("%Y-%m-%d %H:%M")
            
            jql = f'project = {self.project_key} AND updated >= "{since_str}" ORDER BY updated DESC'
            issues = self.jira.search_issues(jql, maxResults=limit)
            
            updates = []
            for issue in issues:
                updates.append(self._format_issue(issue))
            
            logger.info(f"🔄 Found {len(updates)} recent updates in last {hours}h")
            return updates
            
        except Exception as e:
            logger.error(f"Failed to fetch recent updates: {e}")
            return []
    
    def get_issue_by_key(self, issue_key: str) -> Optional[Dict]:
        """Получить задачу по ключу"""
        try:
            issue = self.jira.issue(issue_key)
            return self._format_issue(issue)
        except Exception as e:
            logger.error(f"Failed to fetch issue {issue_key}: {e}")
            return None
    
    def search_issues(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Поиск задач по тексту
        
        Args:
            query: Поисковый запрос
            max_results: Максимум результатов
        """
        try:
            jql = f'project = {self.project_key} AND (summary ~ "{query}" OR description ~ "{query}")'
            issues = self.jira.search_issues(jql, maxResults=max_results)
            return [self._format_issue(issue) for issue in issues]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _format_issue(self, issue) -> Dict:
        """
        Приводит задачу Jira к унифицированному формату
        
        Унифицированный формат нужен для того, чтобы все источники
        (Telegram, Jira, Gmail) возвращали данные в одинаковой структуре.
        Это упрощает работу агента.
        """
        # Получаем приоритет с эмодзи
        priority = issue.fields.priority.name if issue.fields.priority else "Medium"
        priority_emoji = {
            'Highest': '🔴', 'High': '🟠',
            'Medium': '🟡', 'Low': '🟢'
        }.get(priority, '⚪')
        
        # Формируем ссылку на задачу
        issue_link = f"{self.url}/browse/{issue.key}"
        
        # Безопасная обработка дат
        updated = issue.fields.updated
        if hasattr(updated, 'isoformat'):
            updated_str = updated.isoformat()
        else:
            updated_str = str(updated) if updated else None
        
        created = issue.fields.created
        if hasattr(created, 'isoformat'):
            created_str = created.isoformat()
        else:
            created_str = str(created) if created else None
        
        return {
            # Базовые поля (универсальные для всех источников)
            'source': 'jira',
            'source_id': issue.key,
            'title': issue.fields.summary,
            'text': issue.fields.summary,
            'timestamp': updated_str,
            'link': issue_link,
            
            # Специфичные для Jira поля
            'metadata': {
                'key': issue.key,
                'status': issue.fields.status.name,
                'priority': priority,
                'priority_emoji': priority_emoji,
                'assignee': issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned',
                'created': created_str,
                'updated': updated_str,
            }
        }
    

# класс JiraConnector

# Ключевые методы:

# - get_my_tasks(assignee, limit): получает активные задачи пользователя
# - get_recent_updates(hours, limit): находит задачи, обновлённые за последние N часов
# - get_issue_by_key(issue_key): возвращает задачу по ключу (например, PROJ-123)
# - search_issues(query, max_results): ищет задачи по тексту в заголовке и описании
# - validate(): проверяет валидность подключения


# Возвращаемые данные:
# - Приводит задачи Jira к унифицированному формату с полями:
#   source, source_id, title, text, timestamp, link, metadata
# - metadata содержит специфичные поля: статус, приоритет, исполнитель, даты создания/обновления
