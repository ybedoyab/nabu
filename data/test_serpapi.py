"""
Quick standalone script to test the SerpAPI Google Scholar integration.
Edit the variables at the bottom of this file to change the query/limit/mode.
"""

import json
import os
import re
import sys
from typing import Optional, Tuple

import serpapi
from dotenv import load_dotenv

load_dotenv()



def _parse_venue_and_year(summary: str) -> Tuple[Optional[str], Optional[str]]:
    if not summary:
        return None, None
    parts = [p.strip() for p in summary.split(" - ")]
    if len(parts) < 2:
        return None, None
    middle = parts[1] if len(parts) >= 3 else ""
    if not middle:
        return None, None
    year_match = re.search(r"(\d{4})\s*$", middle)
    year = year_match.group(1) if year_match else None
    venue = middle
    if year:
        venue = re.sub(r",?\s*" + year + r"\s*$", "", middle).strip()
    venue = venue or None
    published_at = f"{year}-01-01T00:00:00Z" if year else None
    return venue, published_at


def run(query: str, limit: int, raw: bool) -> None:
    api_key = os.environ.get("SERPAPI_API_KEY")
    if not api_key:
        print("ERROR: SERPAPI_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    client = serpapi.Client(api_key=api_key)
    print(f"\nQuerying Google Scholar: '{query}'  (limit={limit})\n{'─'*60}")

    response = client.search(
        {
            "engine": "google_scholar",
            "q": query,
            "hl": "en",
            "num": limit,
        }
    )

    mocks_dir = os.path.join(os.path.dirname(__file__), "mocks")
    safe_query = re.sub(r"[^\w\-]", "_", query)[:60]
    mock_path = os.path.join(mocks_dir, f"scholar_{safe_query}.json")
    with open(mock_path, "w", encoding="utf-8") as f:
        json.dump(response.get("organic_results", []), f, indent=2, default=str)
    print(f"Response saved → {mock_path}")

    if raw:
        print("\n--- RAW JSON RESPONSE ---")
        print(json.dumps(dict(response), indent=2, default=str))
        return

    organic_results = response.get("organic_results", []) or []
    if not organic_results:
        print("No organic results returned.")
        return

    for i, item in enumerate(organic_results, 1):
        pub_info = item.get("publication_info", {}) or {}
        inline_links = item.get("inline_links", {}) or {}
        resources = item.get("resources", []) or []

        venue, published_at = _parse_venue_and_year(pub_info.get("summary", ""))
        pdf_url = next(
            (r["link"] for r in resources if r.get("file_format") == "PDF"), None
        )
        citation_count = (inline_links.get("cited_by") or {}).get("total")
        authors = [a.get("name", "") for a in pub_info.get("authors", []) or []]

        print(f"[{i}] {item.get('title', '(no title)')}")
        print(f"     result_id  : {item.get('result_id')}")
        print(f"     authors    : {', '.join(authors) or '—'}")
        print(f"     venue      : {venue or '—'}")
        print(f"     published  : {published_at or '—'}")
        print(f"     citations  : {citation_count}")
        print(f"     pdf_url    : {pdf_url or '—'}")
        print(f"     link       : {item.get('link', '—')}")
        print(f"     summary    : {pub_info.get('summary', '—')}")
        print(f"     snippet    : {(item.get('snippet') or '')[:120]}...")
        print()


if __name__ == "__main__":
    # ── Edit these to try different cases ──────────────────────────────────
    QUERY = "machine learning -site:books.google.com -filetype:pdf"
    LIMIT = 10       # 1–20
    RAW   = False   # True → prints the raw JSON response
    # ───────────────────────────────────────────────────────────────────────

    run(query=QUERY, limit=max(1, min(LIMIT, 20)), raw=RAW)
