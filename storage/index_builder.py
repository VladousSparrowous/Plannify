from storage.document_builder import DocumentBuilder
from storage.vector_store import VectorStore


class IndexBuilder:
    def __init__(self, vector_store: VectorStore):
        self.vs = vector_store

    def rebuild_all(self, sources: dict):
        """
        sources = {
            "telegram": [...],
            "jira": [...],
            "calendar": [...]
        }
        """

        all_docs = []

        for source, items in sources.items():
            docs = DocumentBuilder.build_batch(source, items)
            all_docs.extend(docs)

            for doc in docs:
                self.vs.add_document(doc)

        return all_docs