import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


def get_abstract(url: str, timeout: int = 30) -> str:
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[403, 429, 500, 502, 503, 504])
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))

    response = session.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    abstract = soup.find(id="Abs1-content")
    if abstract is None:
        raise ValueError(f"No abstract found at {url}")

    paragraphs = abstract.find_all("p")
    if not paragraphs:
        raise ValueError(f"No abstract paragraphs found at {url}")

    return "\n\n".join(p.get_text(" ", strip=True) for p in paragraphs)


if __name__ == "__main__":
    test_url = "https://www.nature.com/articles/s41565-024-01753-8"
    try:
        abstract = get_abstract(test_url)
        print(abstract)
    except Exception as e:
        print(f"Error fetching abstract: {e}")
