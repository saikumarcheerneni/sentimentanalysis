from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd
import io
import requests
from bs4 import BeautifulSoup
import re

from app.auth import oauth2_scheme, jwt, SECRET_KEY, ALGORITHM


router = APIRouter()


# ---------------------------------------------------------
# JWT TOKEN VALIDATION
# ---------------------------------------------------------
def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(401, "Invalid token")
        return username
    except:
        raise HTTPException(401, "Invalid token")


# ---------------------------------------------------------
# HELPER: CLEAN TEXT
# ---------------------------------------------------------
def clean(text):
    if not text:
        return ""
    return " ".join(text.strip().split())


# ---------------------------------------------------------
# 1️⃣ GENERIC REVIEW SCRAPER
# ---------------------------------------------------------
def extract_generic_reviews(url: str):
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception:
        return []

    possible_tags = ["review", "comment", "feedback", "testimonial"]
    reviews = []

    for tag in soup.find_all(text=True):
        lower = tag.lower()
        if any(keyword in lower for keyword in possible_tags):
            cleaned = clean(tag)
            if len(cleaned.split()) > 3:
                reviews.append(cleaned)

    return list(set(reviews))


# ---------------------------------------------------------
# 2️⃣ AMAZON REVIEW SCRAPER
# ---------------------------------------------------------
def extract_amazon_reviews(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        resp = requests.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception:
        return []

    review_blocks = soup.find_all("span", {"data-hook": "review-body"})
    reviews = [clean(r.text) for r in review_blocks]

    return reviews


# ---------------------------------------------------------
# 3️⃣ FLIPKART SCRAPER
# ---------------------------------------------------------
def extract_flipkart_reviews(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        resp = requests.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception:
        return []

    review_divs = soup.find_all("div", {"class": "t-ZTKy"})
    reviews = [clean(div.text.replace("READ MORE", "")) for div in review_divs]

    return reviews


# ---------------------------------------------------------
# CSV GENERATION
# ---------------------------------------------------------
def generate_csv(reviews):
    df = pd.DataFrame({"text": reviews})

    stream = io.StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)

    return io.BytesIO(stream.getvalue().encode("utf-8"))


# =========================================================
#                  ROUTES START HERE
# =========================================================

# ---------------------------------------------------------
# 4️⃣ Extract GENERIC Reviews → POST /reviews/extract
# ---------------------------------------------------------
@router.post("/reviews/extract", tags=["Review Extraction"])
def extract_to_csv(url: str, username: str = Depends(verify_token)):

    reviews = extract_generic_reviews(url)

    if not reviews:
        raise HTTPException(400, "No reviews were found on this page")

    csv_stream = generate_csv(reviews)

    return StreamingResponse(
        csv_stream,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reviews.csv"}
    )


# ---------------------------------------------------------
# 5️⃣ Extract Amazon Reviews → POST /reviews/amazon
# ---------------------------------------------------------
@router.post("/reviews/amazon", tags=["Review Extraction"])
def extract_amazon_to_csv(url: str, username: str = Depends(verify_token)):

    reviews = extract_amazon_reviews(url)

    if not reviews:
        raise HTTPException(400, "Could not scrape any Amazon reviews.")

    csv_stream = generate_csv(reviews)

    return StreamingResponse(
        csv_stream,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=amazon_reviews.csv"}
    )


# ---------------------------------------------------------
# 6️⃣ Extract Flipkart Reviews → POST /reviews/flipkart
# ---------------------------------------------------------
@router.post("/reviews/flipkart", tags=["Review Extraction"])
def extract_flipkart_to_csv(url: str, username: str = Depends(verify_token)):

    reviews = extract_flipkart_reviews(url)

    if not reviews:
        raise HTTPException(400, "Could not scrape any Flipkart reviews.")

    csv_stream = generate_csv(reviews)

    return StreamingResponse(
        csv_stream,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=flipkart_reviews.csv"}
    )
