from storage.schema import Document


class Normalizer:

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        return " ".join(text.split()).strip()

    @staticmethod
    def enforce(doc: dict) -> Document:
        """
        Приводит любой документ к строгому контракту
        """
        return {
            "id": doc["id"],
            "text": Normalizer.clean_text(doc.get("text", "")),
            "type": doc.get("type", "message"),
            "source": doc.get("source", "unknown"),
            "timestamp": doc.get("timestamp"),
            "link": doc.get("link"),
            "metadata": doc.get("metadata", {})
        }