import requests
from bs4 import BeautifulSoup


def extract_reviews_from_url(url: str) -> list:
    """
    Extracts product reviews from Amazon/Generic e-commerce pages.
    Returns a list of review texts.
    """

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        html = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(html.text, "html.parser")

        review_texts = []

        for span in soup.find_all("span", {"data-hook": "review-body"}):
            text = span.get_text(strip=True)
            if text:
                review_texts.append(text)

        if not review_texts:
            for p in soup.find_all("p"):
                text = p.get_text(strip=True)
                if len(text.split()) > 5:
                    review_texts.append(text)

        return review_texts

    except Exception as e:
        print("URL Scrape Error:", e)
        return []
