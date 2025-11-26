from transformers import pipeline
import json


model = None

def init():
    """
    Initialize the model when the endpoint is started.
    This runs only once per deployment node.
    """
    global model
    model = pipeline("sentiment-analysis")
    print("Model loaded successfully!")

def run(raw_data):
    """
    Handles incoming requests and returns predictions.
    raw_data: The raw POST body as a JSON string.
    """
    try:
        data = json.loads(raw_data)
        
      
        text = data.get("text", None)
        if not text:
            return {"error": "No 'text' field received"}
        
        prediction = model(text)[0]
        
        return {
            "label": prediction["label"],
            "score": float(prediction["score"])
        }
    
    except Exception as e:
       
        return {"error": str(e)}
