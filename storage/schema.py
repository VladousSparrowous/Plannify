from typing import TypedDict, Dict, Any, Optional


class Document(TypedDict):
    id: str
    text: str
    type: str          # message | task | event
    source: str        # telegram | jira | calendar
    timestamp: Optional[str]
    link: Optional[str]
    metadata: Dict[str, Any]