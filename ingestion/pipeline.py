from storage.normalize import Normalizer
from storage.vector_store import VectorStore


class IngestionPipeline:

    def __init__(self, vector_store: VectorStore):
        self.vs = vector_store

    def ingest(self, raw_docs: list):
        """
        raw_docs = output from connectors
        """

        for doc in raw_docs:
            normalized = Normalizer.enforce(doc)
            self.vs.add_document(normalized)