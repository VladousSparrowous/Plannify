from datetime import datetime, timedelta


class DailyDigest:

    def __init__(self, vector_store, retriever):
        self.vs = vector_store
        self.retriever = retriever

    def get_today(self):

        today = datetime.now()
        tomorrow = today + timedelta(days=1)

        # 1. Calendar events (лучший источник для /today)
        calendar_events = self.vs.search_messages("meeting event", limit=20)

        # 2. Jira tasks
        jira_tasks = self.vs.search_similar_tasks("task todo issue", limit=20)

        # 3. Telegram context (через semantic search)
        telegram_msgs = self.vs.search_messages("today plan urgent", limit=20)

        return {
            "tasks": jira_tasks,
            "events": calendar_events,
            "messages": telegram_msgs
        }

    def format_digest(self, data: dict) -> str:

        parts = ["📅 TODAY DIGEST\n"]

        # TASKS
        parts.append("📌 TASKS:")
        if data["tasks"]:
            for i, t in enumerate(data["tasks"][:5], 1):
                parts.append(f"{i}. {t['text']}")
        else:
            parts.append("— no tasks")

        # EVENTS
        parts.append("\n📅 EVENTS:")
        if data["events"]:
            for i, e in enumerate(data["events"][:5], 1):
                parts.append(f"{i}. {e['text']}")
        else:
            parts.append("— no events")

        # MESSAGES
        parts.append("\n💬 MESSAGES:")
        if data["messages"]:
            for i, m in enumerate(data["messages"][:5], 1):
                parts.append(f"{i}. {m['text']}")
        else:
            parts.append("— no messages")

        return "\n".join(parts)
    



#  DailyDigest:
#    - Генерирует сводку на сегодня из разных источников
#    - Использует векторный поиск вместо точных JQL/фильтров
#    - Форматирует вывод для показа пользователю

# Ключевые методы:
#
# get_today():
#    - Собирает данные через семантический поиск
#    - Ищет события календаря по запросу "meeting event"
#    - Ищет задачи Jira по запросу "task todo issue"
#    - Ищет сообщения Telegram по запросу "today plan urgent"
#    - Возвращает словарь с тремя категориями (tasks, events, messages)
#
# format_digest(data):
#    - Форматирует собранные данные в текст
#    - Добавляет заголовок "📅 TODAY DIGEST"
#    - Группирует по категориям с эмодзи: 📌 TASKS, 📅 EVENTS, 💬 MESSAGES
#    - Ограничивает вывод 5 элементами на категорию
#    - При отсутствии данных показывает "— no tasks/events/messages"



# Поисковые запросы:
# - События: "meeting event" (находит встречи, созвоны, митинги)
# - Задачи: "task todo issue" (находит задачи, туду, ишьюсы)
# - Сообщения: "today plan urgent" (находит планы на сегодня, срочное)
#
# Векторные методы:
# - search_messages() — для событий и сообщений (единый метод)
# - search_similar_tasks() — специально для задач Jira


# Формат вывода:
# ```
# 📅 TODAY DIGEST
#
# 📌 TASKS:
# 1. Задача 1
# 2. Задача 2
#
# 📅 EVENTS:
# 1. Встреча в 15:00
#
# 💬 MESSAGES:
# 1. Важное сообщение
# ```
#
# ⚠️ ВАЖНЫЕ ЗАМЕЧАНИЯ И ОГРАНИЧЕНИЯ:
#
# 1. ПРОБЛЕМА С ДАТАМИ:
#    - Код НЕ фильтрует результаты по дате (сегодня/завтра)
#    - calendar_events может вернуть события на любую дату
#    - jira_tasks вернёт задачи без учёта дедлайнов
#    - telegram_msgs вернёт сообщения за всё время
#    - Фактически возвращается "лучшее semantic совпадение", а не "сегодняшнее"
#
# 2. ВРЕМЕННАЯ ФИЛЬТРАЦИЯ ОТСУТСТВУЕТ:
#    - Созданы переменные today/tomorrow, но не используются
#    - Нет передачи временных параметров в векторный поиск
#    - Невозможно получить ТОЛЬКО события/задачи на сегодня
#
# 3. СЕМАНТИЧЕСКИЙ vs СТРУКТУРИРОВАННЫЙ ПОИСК:
#    - Использует семантические запросы вместо точных фильтров
#    - "meeting event" может найти не все события
#    - "task todo issue" может пропустить задачи без этих слов
#    - Более надёжный подход: запрос к Calendar API по дате
#
# 4. СОВЕТЫ ПО УЛУЧШЕНИЮ:
#    ```python
#    # Правильный подход:
#    calendar_events = calendar_connector.get_today_events()
#    jira_tasks = jira_connector.get_my_tasks()
#    telegram_msgs = telegram_connector.get_messages(limit=20, since=today)
#    ```


# Использование:
# digest = DailyDigest(vector_store, retriever)
# data = digest.get_today()
# text = digest.format_digest(data)
# print(text)