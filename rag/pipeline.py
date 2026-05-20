from rag.context_engine import ContextEngine


class RAGPipeline:

    def __init__(self, retriever):
        self.retriever = retriever
        self.context_engine = ContextEngine()

    def run(self, query: str, top_k: int = 5):

        results = self.retriever.retrieve(query, k=top_k)

        context = self.context_engine.build(query, results)

        return {
            "context": context,
            "results": results
        }