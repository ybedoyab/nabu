from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Article:
    id: str
    title: str
    url: str
    relevance_score: float = 0.0
    relevance_reasons: List[str] = field(default_factory=list)
    research_applications: List[str] = field(default_factory=list)
    organisms: List[str] = field(default_factory=list)
    key_concepts: List[str] = field(default_factory=list)
    selected: bool = False


@dataclass
class ResearchSession:
    research_query: str
    selected_articles: List[Dict[str, Any]] = field(default_factory=list)
    chat_history: List[Dict[str, Any]] = field(default_factory=list)
