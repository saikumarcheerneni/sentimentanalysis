from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from app.models import SentimentRequest, SentimentResponse
from app.sentiment_service import analyze_text
from app.database import collection
from app.auth import oauth2_scheme, jwt, SECRET_KEY, ALGORITHM
import tempfile
from app.blob_service import upload_file_to_blob
import pandas as pd

router = APIRouter()


def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return username
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# -------------------------------------------------------------
#  SINGLE TEXT ANALYSIS (Prevent Duplicate Entry)
# -------------------------------------------------------------
@router.post("/analyze", response_model=SentimentResponse)
def analyze_sentiment(request: SentimentRequest, username: str = Depends(verify_token)):
    # 🔍 Check if duplicate exists
    existing = collection.find_one({"user": username, "text": request.text})
    if existing:
        raise HTTPException(status_code=409, detail="Duplicate entry: this text already analyzed")

    result = analyze_text(request.text)

    collection.insert_one({
        "user": username,
        "text": request.text,
        "label": result["label"],
        "score": result["score"]
    })

    return {
        "text": request.text,
        "label": result["label"],
        "score": result["score"]
    }


# -------------------------------------------------------------
#  HISTORY (no change)
# -------------------------------------------------------------
@router.get("/history")
def get_history(username: str = Depends(verify_token)):
    data = list(collection.find({"user": username}, {"_id": 0, "user": 0}))
    return {"history": data}


# -------------------------------------------------------------
#  CSV UPLOAD ANALYSIS (Skip Duplicate Entries)
# -------------------------------------------------------------
@router.post("/upload_csv")
async def upload_csv(file: UploadFile = File(...), username: str = Depends(verify_token)):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    # Upload file to Azure Blob
    upload_file_to_blob(tmp_path, f"{username}_{file.filename}")

    df = pd.read_csv(tmp_path)
    inserted_count = 0
    skipped_count = 0

    for text in df["text"]:
        # 🔍 Prevent duplicates for CSV
        if collection.find_one({"user": username, "text": text}):
            skipped_count += 1
            continue

        result = analyze_text(text)
        collection.insert_one({
            "user": username,
            "text": text,
            "label": result["label"],
            "score": result["score"]
        })

        inserted_count += 1

    return {
        "message": f"CSV processed for {username}",
        "inserted": inserted_count,
        "skipped_duplicates": skipped_count,
        "total_rows": len(df)
    }

# -------------------------------------------------------------
#  DELETE A SINGLE TEXT FOR LOGGED-IN USER
# -------------------------------------------------------------
@router.delete("/delete_text")
def delete_text(text: str, username: str = Depends(verify_token)):
    """
    Delete one analyzed text for the current user.

    Usage:
      DELETE /delete_text?text=I%20am%20happy
      Header: Authorization: Bearer <token>
    """
    result = collection.delete_one({"user": username, "text": text})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Text not found for this user"
        )

    return {"message": "Text deleted successfully", "text": text}

