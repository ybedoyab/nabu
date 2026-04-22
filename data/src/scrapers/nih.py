import requests
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


def get_abstract(url: str, timeout: int = 30) -> str:
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    abstract_section = soup.find("section", class_="abstract")
    if abstract_section is None:
        raise ValueError(f"No abstract section found at {url}")

    paragraphs = abstract_section.find_all("p")
    if not paragraphs:
        raise ValueError(f"Abstract section has no paragraphs at {url}")

    return "\n\n".join(p.get_text(" ", strip=True) for p in paragraphs)

if __name__ == "__main__":
    test_url = "https://pmc.ncbi.nlm.nih.gov/articles/PMC5905345/"
    try:
        abstract = get_abstract(test_url)
        print(abstract)
    except Exception as e:
        print(f"Error fetching abstract: {e}")
