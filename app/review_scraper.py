# import time
# import re
# import requests
# from bs4 import BeautifulSoup

# # Selenium
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from webdriver_manager.chrome import ChromeDriverManager

# # User agent for requests fallback
# HEADERS = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
#     "Accept-Language": "en-US,en;q=0.9"
# }


# # --------------------------------------------------------------------
# # HELPERS
# # --------------------------------------------------------------------

# def clean_text(text: str) -> str:
#     """Remove HTML spaces, emojis, weird characters."""
#     text = re.sub(r"\s+", " ", text).strip()
#     return text


# # --------------------------------------------------------------------
# # SELENIUM SCRAPER (BEST ACCURACY)
# # --------------------------------------------------------------------

# def extract_reviews_selenium(url: str, max_pages: int = 5):
#     """Extract reviews using Selenium — supports dynamic pages."""
#     options = Options()
#     options.add_argument("--headless=new")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")

#     driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

#     reviews = []
#     current_url = url

#     for _ in range(max_pages):
#         driver.get(current_url)
#         time.sleep(2)

#         soup = BeautifulSoup(driver.page_source, "html.parser")

#         # Amazon
#         amazon_reviews = soup.select("span[data-hook='review-body']")
#         if amazon_reviews:
#             for r in amazon_reviews:
#                 text = clean_text(r.get_text())
#                 if text:
#                     reviews.append(text)

#         # Flipkart
#         flip_reviews = soup.select("div._6K-7Co")
#         if flip_reviews:
#             for r in flip_reviews:
#                 text = clean_text(r.get_text())
#                 if text:
#                     reviews.append(text)

#         # BestBuy
#         bb_reviews = soup.select("p.pre-white-space")
#         if bb_reviews:
#             for r in bb_reviews:
#                 text = clean_text(r.get_text())
#                 if text:
#                     reviews.append(text)

#         # Walmart
#         wm_reviews = soup.select("span.review-text")
#         if wm_reviews:
#             for r in wm_reviews:
#                 text = clean_text(r.get_text())
#                 if text:
#                     reviews.append(text)

#         # Next page button (Amazon only)
#         next_btn = soup.select_one("li.a-last a")
#         if next_btn:
#             current_url = "https://www.amazon.in" + next_btn["href"]
#         else:
#             break

#     driver.quit()

#     return list(dict.fromkeys(reviews))  # remove duplicates


# # --------------------------------------------------------------------
# # REQUESTS-BASED SCRAPER (fallback)
# # --------------------------------------------------------------------

# def extract_reviews_requests(url: str):
#     """Fallback simple scraper using requests."""
#     try:
#         res = requests.get(url, headers=HEADERS, timeout=10)
#         if res.status_code != 200:
#             return []
#     except:
#         return []

#     soup = BeautifulSoup(res.text, "html.parser")
#     reviews = []

#     # Amazon
#     for r in soup.select("span.review-text-content"):
#         reviews.append(clean_text(r.get_text(strip=True)))

#     # Flipkart
#     for r in soup.select("div._6K-7Co"):
#         reviews.append(clean_text(r.get_text(strip=True)))

#     # BestBuy
#     for r in soup.select("p.pre-white-space"):
#         reviews.append(clean_text(r.get_text(strip=True)))

#     # Walmart
#     for r in soup.select("span.review-text"):
#         reviews.append(clean_text(r.get_text(strip=True)))

#     return list(dict.fromkeys(reviews))


# # --------------------------------------------------------------------
# # MASTER SCRAPER (DECIDES AUTOMATICALLY BASED ON SITE)
# # --------------------------------------------------------------------

# def extract_reviews_from_url(url: str, max_pages: int = 5):
#     """Decides automatically the best scraping method for the site."""
#     url = url.strip()

#     # Amazon needs Selenium for full pagination
#     if "amazon" in url:
#         return extract_reviews_selenium(url, max_pages=max_pages)

#     # Other sites work fine with requests
#     reviews = extract_reviews_requests(url)
#     return reviews

import time
import re
import requests
from bs4 import BeautifulSoup

# Selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# User agent for requests fallback
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9"
}


# --------------------------------------------------------------------
# HELPERS
# --------------------------------------------------------------------
def clean_text(text: str) -> str:
    """Remove HTML spaces, emojis, weird characters."""
    text = re.sub(r"\s+", " ", text).strip()
    return text


# --------------------------------------------------------------------
# SELENIUM SCRAPER (FIXED VERSION)
# --------------------------------------------------------------------
def extract_reviews_selenium(url: str, max_pages: int = 5):
    """Extract reviews using Selenium — supports dynamic pages."""

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # ❗❗ FIX: correct Selenium initialization
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    reviews = []
    current_url = url

    for _ in range(max_pages):
        driver.get(current_url)
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Amazon
        amazon_reviews = soup.select("span[data-hook='review-body']")
        for r in amazon_reviews:
            text = clean_text(r.get_text())
            if text:
                reviews.append(text)

        # Flipkart
        flip_reviews = soup.select("div._6K-7Co")
        for r in flip_reviews:
            text = clean_text(r.get_text())
            if text:
                reviews.append(text)

        # BestBuy
        bb_reviews = soup.select("p.pre-white-space")
        for r in bb_reviews:
            text = clean_text(r.get_text())
            if text:
                reviews.append(text)

        # Walmart
        wm_reviews = soup.select("span.review-text")
        for r in wm_reviews:
            text = clean_text(r.get_text())
            if text:
                reviews.append(text)

        # Amazon next page
        next_btn = soup.select_one("li.a-last a")
        if next_btn:
            current_url = "https://www.amazon.in" + next_btn["href"]
        else:
            break

    driver.quit()

    return list(dict.fromkeys(reviews))  # remove duplicates


# --------------------------------------------------------------------
# REQUESTS-BASED SCRAPER (fallback)
# --------------------------------------------------------------------
def extract_reviews_requests(url: str):
    """Fallback simple scraper using requests."""
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return []
    except:
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    reviews = []

    # Amazon
    for r in soup.select("span.review-text-content"):
        reviews.append(clean_text(r.get_text(strip=True)))

    # Flipkart
    for r in soup.select("div._6K-7Co"):
        reviews.append(clean_text(r.get_text(strip=True)))

    # BestBuy
    for r in soup.select("p.pre-white-space"):
        reviews.append(clean_text(r.get_text(strip=True)))

    # Walmart
    for r in soup.select("span.review-text"):
        reviews.append(clean_text(r.get_text(strip=True)))

    return list(dict.fromkeys(reviews))


# --------------------------------------------------------------------
# MASTER SCRAPER
# --------------------------------------------------------------------
def extract_reviews_from_url(url: str, max_pages: int = 5):
    """Decides automatically the best scraping method for the site."""
    url = url.strip()

    # Amazon → use Selenium (pagination)
    if "amazon" in url:
        return extract_reviews_selenium(url, max_pages=max_pages)

    # Others → requests only
    return extract_reviews_requests(url)
