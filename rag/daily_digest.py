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