import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from ...domain.entities import ArticleRecord, SessionFetchResult
from ...ports.search_provider_port import SearchProviderPort


class FetchSessionUseCase:
    def __init__(self, providers: List[SearchProviderPort], ttl_seconds: int = 3600):
        self.providers = providers
        self.ttl_seconds = ttl_seconds

    def execute(self, query: str, limits: Dict[str, int]) -> SessionFetchResult:
        session_id = f"sess_{uuid.uuid4().hex}"
        expires_at = (
            datetime.now(tz=timezone.utc) + timedelta(seconds=self.ttl_seconds)
        ).replace(microsecond=0).isoformat().replace("+00:00", "Z")

        articles: List[ArticleRecord] = []
        errors_by_source: Dict[str, Dict[str, str]] = {}
        raw_counts = {"arxiv": 0, "scholar": 0}

        for provider in self.providers:
            source = provider.source_name
            limit = int(limits.get(source, 0) or 0)
            if limit <= 0:
                continue
            try:
                found = provider.search(query=query, limit=limit)
                raw_counts[source] = len(found)
                articles.extend(found)
            except Exception as exc:
                errors_by_source[source] = {
                    "code": "FETCH_FAILED",
                    "message": str(exc),
                }

        merged = self._deduplicate(articles)
        duplicates_removed = max(len(articles) - len(merged), 0)
        status = "partial" if errors_by_source else "ok"

        return SessionFetchResult(
            status=status,
            session_id=session_id,
            query=query,
            ttl_seconds=self.ttl_seconds,
            expires_at=expires_at,
            sources_queried=[p.source_name for p in self.providers if int(limits.get(p.source_name, 0) or 0) > 0],
            limits_applied={"arxiv": int(limits.get("arxiv", 0) or 0), "scholar": int(limits.get("scholar", 0) or 0)},
            stats={
                "raw_arxiv": raw_counts.get("arxiv", 0),
                "raw_scholar": raw_counts.get("scholar", 0),
                "merged_unique": len(merged),
                "duplicates_removed": duplicates_removed,
            },
            articles=merged,
            errors_by_source=errors_by_source,
        )

    @staticmethod
    def _deduplicate(articles: List[ArticleRecord]) -> List[ArticleRecord]:
        seen = set()
        out: List[ArticleRecord] = []
        for article in articles:
            key_src = article.landing_url.strip().lower() or article.external_id.strip().lower()
            key = hashlib.sha256(key_src.encode("utf-8")).hexdigest()
            if key in seen:
                continue
            seen.add(key)
            out.append(article)
        return out
