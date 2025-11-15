from transformers import pipeline

# Lazy load model to prevent Azure startup timeout
sentiment_model = None

def get_model():
    global sentiment_model
    if sentiment_model is None:
        sentiment_model = pipeline("sentiment-analysis")
    return sentiment_model

def analyze_text(text: str):
    """
    Analyze the sentiment of input text.
    Returns label (POSITIVE/NEGATIVE) and score.
    """
    model = get_model()
    result = model(text)[0]
    return {"label": result["label"], "score": result["score"]}
