from collections import defaultdict


class ContextEngine:

    def build(self, query: str, results: list) -> str:
        """
        Превращает raw retrieval в структурированный контекст
        """

        grouped = defaultdict(list)

        for r in results:
            meta = r.get("metadata", {})
            source = meta.get("source", "unknown")

            grouped[source].append(r)

        parts = []

        # 1. Tasks (Jira) — highest priority
        if grouped.get("jira"):
            parts.append("📌 TASKS:")
            for i, r in enumerate(grouped["jira"], 1):
                parts.append(f"{i}. {r['text']}")

        # 2. Calendar — second priority
        if grouped.get("google_calendar"):
            parts.append("\n📅 EVENTS:")
            for i, r in enumerate(grouped["google_calendar"], 1):
                parts.append(f"{i}. {r['text']}")

        # 3. Telegram — lowest priority
        if grouped.get("telegram"):
            parts.append("\n💬 MESSAGES:")
            for i, r in enumerate(grouped["telegram"], 1):
                parts.append(f"{i}. {r['text']}")

        # fallback (если нет metadata)
        if not parts:
            for i, r in enumerate(results, 1):
                parts.append(f"{i}. {r['text']}")

        return "\n".join(parts)