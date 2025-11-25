# from transformers import pipeline

# # Lazy load model to prevent Azure startup timeout
# sentiment_model = None

# def get_model():
#     global sentiment_model
#     if sentiment_model is None:
#         sentiment_model = pipeline("sentiment-analysis", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")
#     return sentiment_model

# def analyze_text(text: str):
#     """
#     Analyze the sentiment of input text.
#     Returns label (POSITIVE/NEGATIVE) and score.
#     """
#     model = get_model()
#     result = model(text)[0]
#     return {"label": result["label"], "score": result["score"]}
from transformers import pipeline, AutoTokenizer
from typing import List, Dict, Any

# Lazy load the model only once (Azure optimization)
sentiment_model = None
tokenizer = None


def normalize_label(label: str) -> str:
    """
    Convert HuggingFace labels into standard format:
        LABEL_0 → NEGATIVE
        LABEL_1 → NEUTRAL
        LABEL_2 → POSITIVE
    
    Or handle textual labels:
        "negative" → NEGATIVE
        "neutral" → NEUTRAL
        "positive" → POSITIVE
    """
    label = label.lower()

    if label in ["label_0", "negative"]:
        return "NEGATIVE"
    if label in ["label_1", "neutral"]:
        return "NEUTRAL"
    if label in ["label_2", "positive"]:
        return "POSITIVE"

    return label.upper()  # fallback


def get_model():
    """
    Loads the HuggingFace multilingual RoBERTa sentiment model only once.
    Prevents Azure cold-start slowdowns.
    """
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


def analyze_text(text: str) -> Dict[str, Any]:
    """
    Analyze a single text and return:
        {
            "label": "POSITIVE/NEGATIVE/NEUTRAL",
            "score": 0.998
        }
    """
    model = get_model()
    result = model(text)[0]

    normalized = normalize_label(result["label"])

    return {
        "label": normalized,
        "score": float(result["score"])
    }


def analyze_many(texts: List[str]) -> List[Dict[str, Any]]:
    """
    Batch sentiment analysis for faster CSV processing.
    """
    if not texts:
        return []

    model = get_model()
    outputs = model(texts)

    return [
        {
            "label": normalize_label(o["label"]),
            "score": float(o["score"])
        }
        for o in outputs
    ]


def build_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build summary stats used in Excel and email.
    Automatically uses normalized labels.
    """
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

    # Determine overall sentiment
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
