import json
import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}

_METADATA_RE = re.compile(r"xplGlobal\.document\.metadata\s*=\s*(\{.*?\});", re.DOTALL)


def get_abstract(url: str, timeout: int = 30) -> str:
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[403, 429, 500, 502, 503, 504])
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))

    response = session.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()

    match = _METADATA_RE.search(response.text)
    if not match:
        raise ValueError(f"No metadata script found at {url}")

    metadata = json.loads(match.group(1))
    abstract = metadata.get("abstract", "").strip()
    if not abstract:
        raise ValueError(f"Empty abstract at {url}")

    return abstract


if __name__ == "__main__":
    test_url = "https://ieeexplore.ieee.org/abstract/document/5362936"
    try:
        abstract = get_abstract(test_url)
        print(abstract)
    except Exception as e:
        print(f"Error fetching abstract: {e}")
