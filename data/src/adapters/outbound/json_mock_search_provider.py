import json
from pathlib import Path
from typing import List

from ...domain.entities import ArticleRecord, Author, utc_now_iso


class JsonMockSearchProvider:
    def __init__(self, source_name: str, json_path: str):
        self.source_name = source_name
        self.json_path = Path(json_path)

    def search(self, query: str, limit: int) -> List[ArticleRecord]:
        if not self.json_path.exists():
            return []

        raw = json.loads(self.json_path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            return []

        query_terms = [t.strip().lower() for t in query.split() if t.strip()]
        ranked = []

        for item in raw:
            title = str(item.get("title", "")).strip()
            abstract = str(item.get("abstract", "")).strip()
            snippet = str(item.get("snippet", "")).strip()
            haystack = f"{title} {abstract} {snippet}".lower()
            score = sum(1 for term in query_terms if term in haystack)
            if query_terms and score == 0:
                continue
            ranked.append((score, item))

        ranked.sort(key=lambda x: x[0], reverse=True)
        selected = ranked[: max(1, min(limit, len(ranked)))] if ranked else []

        records: List[ArticleRecord] = []
        for _, item in selected:
            authors = [
                Author(
                    name=str(a.get("name", "")).strip(),
                    affiliation=a.get("affiliation"),
                )
                for a in item.get("authors", [])
                if str(a.get("name", "")).strip()
            ]

            record = ArticleRecord(
                corpus_id=str(item.get("corpus_id", "")).strip(),
                source=str(item.get("source", self.source_name)).strip(),
                external_id=str(item.get("external_id", "")).strip(),
                title=str(item.get("title", "")).strip(),
                abstract=str(item.get("abstract", "")).strip(),
                snippet=str(item.get("snippet", "")).strip(),
                authors=authors,
                published_at=item.get("published_at"),
                updated_at=item.get("updated_at"),
                landing_url=str(item.get("landing_url", "")).strip(),
                pdf_url=item.get("pdf_url"),
                categories=item.get("categories", []) or [],
                keywords=item.get("keywords", []) or [],
                venue=item.get("venue"),
                citation_count=item.get("citation_count"),
                snippet_is_partial=bool(item.get("snippet_is_partial", False)),
                authors_incomplete=bool(item.get("authors_incomplete", False)),
                fetched_at=str(item.get("fetched_at", "")).strip() or utc_now_iso(),
            )
            records.append(record)
        return records
