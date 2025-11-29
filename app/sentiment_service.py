from transformers import pipeline, AutoTokenizer
from typing import List, Dict, Any


sentiment_model = None
tokenizer = None

MAX_TOKENS = 250   # prevent model crash


def normalize_label(label: str) -> str:
    label = label.lower()

    if label in ["label_0", "negative"]:
        return "NEGATIVE"
    if label in ["label_1", "neutral"]:
        return "NEUTRAL"
    if label in ["label_2", "positive"]:
        return "POSITIVE"

    return label.upper()


def get_model():
    global sentiment_model, tokenizer
    if sentiment_model is None:
        model_name = "cardiffnlp/twitter-xlm-roberta-base-sentiment"

        tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
        sentiment_model = pipeline(
            "sentiment-analysis",
            model=model_name,
            tokenizer=tokenizer
        )

    return sentiment_model


def _truncate_text(text: str) -> str:
    """
    HARD FIX: Prevent XLM-R from crashing with long inputs.
    """
    # Convert to string
    if not isinstance(text, str):
        text = str(text)

    # Tokenize to count tokens safely
    tokens = tokenizer.encode(text, add_special_tokens=False)

    # If too long → truncate tokens
    if len(tokens) > MAX_TOKENS:
        tokens = tokens[:MAX_TOKENS]
        text = tokenizer.decode(tokens, skip_special_tokens=True)

    return text


def analyze_text(text: str) -> Dict[str, Any]:
    """
    SAFE SINGLE SENTENCE ANALYSIS
    """
    model = get_model()

    # 👇 CRASH PREVENTION FIX
    text = _truncate_text(text)

    result = model(text)[0]
    return {
        "label": normalize_label(result["label"]),
        "score": float(result["score"])
    }


def analyze_many(texts: List[str]) -> List[Dict[str, Any]]:
    """
    SAFE BATCH PROCESSING FOR CSV FILES
    """
    if not texts:
        return []

    model = get_model()

    # 👇 PREVENT CRASH BY TRUNCATING ALL TEXTS FIRST
    cleaned = [_truncate_text(t) for t in texts]

    outputs = model(cleaned)

    return [
        {
            "label": normalize_label(o["label"]),
            "score": float(o["score"])
        }
        for o in outputs
    ]


def build_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    if total == 0:
        return {
            "total": 0,
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "overall": None,
        }

    pos = sum(1 for r in results if r["label"] == "POSITIVE")
    neg = sum(1 for r in results if r["label"] == "NEGATIVE")
    neu = sum(1 for r in results if r["label"] == "NEUTRAL")

    if pos > neg:
        overall = "POSITIVE"
    elif neg > pos:
        overall = "NEGATIVE"
    else:
        overall = "MIXED"

    return {
        "total": total,
        "positive": pos,
        "negative": neg,
        "neutral": neu,
        "overall": overall,
    }
