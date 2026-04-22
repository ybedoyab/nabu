import hashlib
import re
from typing import List
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

from ...domain.entities import ArticleRecord, Author
from ...infrastructure.logger import setup_scraper_logger
import os

class GoogleScholarSearchProvider:
    source_name = "scholar"
    _base_url = "https://scholar.google.com"
    
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        log_dir = os.path.join(base_dir, "webscraping", "logs", "scholar")
        self.logger = setup_scraper_logger("scholar_provider", log_dir)
        self.logger.info("GoogleScholarSearchProvider instantiated.")

    def search(self, query: str, limit: int) -> List[ArticleRecord]:
        self.logger.info(f"Fetching Google Scholar data for query: '{query}' (limit={limit})")
        url = f"{self._base_url}/scholar?q={quote(query)}&hl=en"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; NabuBot/1.0; +https://example.local)"}
        
        try:
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
        except Exception as e:
            self.logger.error(f"Error fetching data from Google Scholar: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.select("div.gs_r.gs_or.gs_scl")[: max(1, min(limit, 20))]

        records: List[ArticleRecord] = []
        for item in results:
            title_tag = item.select_one("h3.gs_rt")
            if not title_tag:
                continue

            anchor = title_tag.find("a")
            title = title_tag.get_text(" ", strip=True)
            landing_url = anchor.get("href", "") if anchor else ""

            snippet_tag = item.select_one("div.gs_rs")
            snippet = snippet_tag.get_text(" ", strip=True) if snippet_tag else ""

            meta_tag = item.select_one("div.gs_a")
            meta_text = meta_tag.get_text(" ", strip=True) if meta_tag else ""
            authors = self._parse_authors(meta_text)
            year = self._parse_year(meta_text)

            external_id = hashlib.sha256((landing_url or title).encode("utf-8")).hexdigest()[:16]
            corpus_id = f"sha256:scholar:{hashlib.sha256(external_id.encode('utf-8')).hexdigest()}"

            records.append(
                ArticleRecord(
                    corpus_id=corpus_id,
                    source="scholar",
                    external_id=external_id,
                    title=title,
                    snippet=snippet,
                    authors=authors,
                    published_at=f"{year}-01-01T00:00:00Z" if year else None,
                    landing_url=landing_url,
                    snippet_is_partial=True,
                    authors_incomplete=True,
                )
            )
        return records

    @staticmethod
    def _parse_authors(meta: str) -> List[Author]:
        if not meta:
            return []
        left = meta.split(" - ")[0]
        names = [n.strip() for n in left.split(",") if n.strip()]
        return [Author(name=n) for n in names[:5]]

    @staticmethod
    def _parse_year(meta: str) -> str | None:
        match = re.search(r"(19|20)\d{2}", meta or "")
        return match.group(0) if match else None
