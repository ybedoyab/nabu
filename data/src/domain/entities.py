from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class Author:
    name: str
    affiliation: Optional[str] = None


@dataclass
class ArticleRecord:
    corpus_id: str
    source: str
    external_id: str
    title: str
    abstract: str = ""
    snippet: str = ""
    authors: List[Author] = field(default_factory=list)
    published_at: Optional[str] = None
    updated_at: Optional[str] = None
    landing_url: str = ""
    pdf_url: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    venue: Optional[str] = None
    citation_count: Optional[int] = None
    snippet_is_partial: bool = False
    authors_incomplete: bool = False
    fetched_at: str = field(default_factory=utc_now_iso)


@dataclass
class SessionFetchResult:
    status: str
    session_id: str
    query: str
    ttl_seconds: int
    expires_at: str
    sources_queried: List[str]
    limits_applied: dict
    stats: dict
    articles: List[ArticleRecord]
    errors_by_source: dict
