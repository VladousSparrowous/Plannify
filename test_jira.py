import asyncio
from config import Config
from connectors.jira import JiraConnector

def test_jira():
    Config.validate()
    
    if not Config.JIRA_TOKEN:
        print("❌ Jira не настроена. Добавьте JIRA_TOKEN в .env")
        return
    
    connector = JiraConnector(
        url=Config.JIRA_URL,
        email=Config.JIRA_EMAIL,
        token=Config.JIRA_TOKEN,
        project_key=Config.JIRA_PROJECT_KEY
    )
    
    # Проверяем подключение
    if connector.validate():
        print("\n📋 Ваши активные задачи:")
        tasks = connector.get_my_tasks()
        for task in tasks:
            print(f"  {task['source_id']}: {task['title'][:50]}...")
    
if __name__ == "__main__":
    test_jira()