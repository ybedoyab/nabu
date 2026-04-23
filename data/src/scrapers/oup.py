from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth


def get_abstract(url: str, timeout: int = 60000) -> str:
    with Stealth().use_sync(sync_playwright()) as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            viewport={"width": 1366, "height": 768},
        )
        page = context.new_page()
        try:
            page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            page.wait_for_selector("#ContentTab section p", timeout=timeout)
            html = page.content()
        finally:
            context.close()
            browser.close()

    soup = BeautifulSoup(html, "lxml")

    content_tab = soup.find(id="ContentTab")
    if content_tab is None:
        raise ValueError(f"No ContentTab found at {url}")

    section = content_tab.find("section")
    if section is None:
        raise ValueError(f"No abstract section found at {url}")

    paragraphs = section.find_all("p")
    if not paragraphs:
        raise ValueError(f"No abstract paragraphs found at {url}")

    return "\n\n".join(p.get_text(" ", strip=True) for p in paragraphs)


if __name__ == "__main__":
    test_url = "https://academic.oup.com/aje/article-abstract/188/12/2222/5567515"
    try:
        abstract = get_abstract(test_url)
        print(abstract)
    except Exception as e:
        print(f"Error fetching abstract: {e}")
