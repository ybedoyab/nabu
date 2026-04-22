import hashlib
import xml.etree.ElementTree as ET
from typing import List
from urllib.parse import quote

import requests

from ...domain.entities import ArticleRecord, Author


class ArxivSearchProvider:
    source_name = "arxiv"
    _endpoint = "https://export.arxiv.org/api/query"

    def search(self, query: str, limit: int) -> List[ArticleRecord]:
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max(1, min(limit, 50)),
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        response = requests.get(self._endpoint, params=params, timeout=20)
        response.raise_for_status()

        root = ET.fromstring(response.text)
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

        records: List[ArticleRecord] = []
        for entry in root.findall("atom:entry", ns):
            raw_id = (entry.findtext("atom:id", default="", namespaces=ns) or "").strip()
            external_id = raw_id.split("/abs/")[-1] if "/abs/" in raw_id else raw_id
            title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip().replace("\n", " ")
            abstract = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip().replace("\n", " ")
            published = entry.findtext("atom:published", default=None, namespaces=ns)
            updated = entry.findtext("atom:updated", default=None, namespaces=ns)

            links = entry.findall("atom:link", ns)
            landing_url = raw_id
            pdf_url = None
            for link in links:
                href = link.attrib.get("href")
                rel = link.attrib.get("rel")
                typ = link.attrib.get("type", "")
                if rel == "alternate" and href:
                    landing_url = href
                if typ == "application/pdf" and href:
                    pdf_url = href

            categories = [c.attrib.get("term", "") for c in entry.findall("atom:category", ns) if c.attrib.get("term")]
            authors = [
                Author(name=(a.findtext("atom:name", default="", namespaces=ns) or "").strip())
                for a in entry.findall("atom:author", ns)
                if (a.findtext("atom:name", default="", namespaces=ns) or "").strip()
            ]

            corpus_id = f"sha256:arxiv:{hashlib.sha256(external_id.encode('utf-8')).hexdigest()}"
            records.append(
                ArticleRecord(
                    corpus_id=corpus_id,
                    source="arxiv",
                    external_id=external_id,
                    title=title,
                    abstract=abstract,
                    authors=authors,
                    published_at=published,
                    updated_at=updated,
                    landing_url=landing_url,
                    pdf_url=pdf_url,
                    categories=categories,
                )
            )
        return records
