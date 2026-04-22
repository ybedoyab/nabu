from typing import List, Protocol

from ..domain.entities import ArticleRecord


class SearchProviderPort(Protocol):
    source_name: str

    def search(self, query: str, limit: int) -> List[ArticleRecord]:
        ...
