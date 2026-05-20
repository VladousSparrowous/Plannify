from storage.normalize import Normalizer


class CronSync:

    def __init__(self, connectors, vector_store, bm25_store):
        self.connectors = connectors
        self.vs = vector_store
        self.bm25 = bm25_store

    def sync_all(self):

        all_docs = []

        # Telegram (Telethon)
        tg_docs = self.connectors["telegram"]
        all_docs += tg_docs

        # Jira
        jira_docs = self.connectors["jira"]
        all_docs += jira_docs

        # Calendar
        cal_docs = self.connectors["calendar"]
        all_docs += cal_docs

        # normalize + index
        normalized = [Normalizer.enforce(d) for d in all_docs]

        for doc in normalized:
            self.vs.add_document(doc)

        # rebuild BM25
        self.bm25.rebuild([
            {"text": d["text"], "metadata": d["metadata"]}
            for d in normalized
        ])

        return len(normalized)