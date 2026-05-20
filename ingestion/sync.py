class DataSync:

    def __init__(self, vector_store, bm25_builder):
        self.vs = vector_store
        self.bm25 = bm25_builder

    def sync(self, docs: list):

        for doc in docs:
            self.vs.add_document(doc)

        # BM25 rebuild (пока просто полный rebuild)
        self.bm25.rebuild()