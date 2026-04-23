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

    section = soup.find("section", class_="abstract")
    if section is None:
        raise ValueError(f"No abstract found at {url}")

    label = section.find("h2")
    if label is not None:
        label.decompose()

    abstract = section.get_text(" ", strip=True)
    if not abstract:
        raise ValueError(f"Empty abstract at {url}")

    return abstract


if __name__ == "__main__":
    test_url = "https://ojs.aaai.org/index.php/AAAI/article/view/17371"
    try:
        abstract = get_abstract(test_url)
        print(abstract)
    except Exception as e:
        print(f"Error fetching abstract: {e}")
