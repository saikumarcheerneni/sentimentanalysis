import requests
import os
import json
from dotenv import load_dotenv

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path=ENV_PATH)

AZURE_ML_ENDPOINT = os.getenv("AZURE_ML_ENDPOINT")
AZURE_ML_KEY = os.getenv("AZURE_ML_KEY")

def analyze_text(text: str):

    # ----- Validate ENV -----
    if not AZURE_ML_ENDPOINT or not AZURE_ML_KEY:
        return {
            "error": "Missing AZURE_ML_ENDPOINT or AZURE_ML_KEY"
        }

    # ----- Azure ML headers -----
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AZURE_ML_KEY}"   # key authentication
    }

    # ----- EXACT PAYLOAD THAT score.py expects -----
    payload = {"text": text}

    print("\n🔵 Sending to Azure ML:", AZURE_ML_ENDPOINT)
    print("🔵 Payload:", payload)

    try:
        response = requests.post(
            AZURE_ML_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=20
        )

        print("🔵 Azure ML Status Code:", response.status_code)
        print("🔵 Azure ML Raw Response:", response.text)

        # Azure ML error
        if response.status_code != 200:
            return {
                "error": f"Azure ML Error {response.status_code}",
                "raw": response.text
            }

        # Parse JSON safely
        return response.json()

    except Exception as e:
        return {
            "error": f"Request failed: {str(e)}"
        }
