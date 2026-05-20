<img width="934" height="934" alt="fabula-ai" src="https://github.com/user-attachments/assets/63d9c8c1-d9ec-4851-ab76-0581fd86a93b" />

**Plannify** — это платформа, которая объединяет внутренние источники — электронную почту, чаты, заметки о совещаниях, трекеры — и предоставляет структурированную, 
полезную для принятия решений информацию вместо избытка необработанных данных. 

Цель проекта в создании единой интеллектуальной платформы, которая агрегирует
корпоративные коммуникации из разных каналов (почта, мессенджеры, CRM, задачи)
и преобразует неструктурированные потоки данных в структурированные информационные сводки, снижая информационную перегрузку сотрудников.
С помощью средств Generative AI происходит автоматическая суммаризация сообщений, извлечение задач, решений и дедлайнов из источников, семантический поиск и
формирование персонализированного ежедневного дайджеста.

MVP проекта это Telegram-бот на базе Google Gemini AI, который объединяет рабочие коммуникации и задачи в едином интерфейсе. 
Бот анализирует переписки в Telegram-чатах и задачи в Jira, помогая пользователю не пропускать важное и эффективно планировать рабочий день.


**Для запуска нужно создать файл:**


**.env**


```
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHATS_TO_READ=[...]

# Jira
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_TOKEN=your_api_token
JIRA_PROJECT_KEY=PROJ

# Google Calendar
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_TOKEN_PATH=token.pickle

# Gemini AI
GEMINI_API_KEY=your_gemini_key

# RAG
RAG_PERSIST_DIR='./data/chroma'
EMBEDDING_MODEL='intfloat/multilingual-e5-small'
```


,установить зависимости активация окружения


```
uv sync

# Создание venv
uv venv

# Активация
# Windows:
.venv\Scripts\activate

# macOS / Linux:
source .venv/bin/activate
```
