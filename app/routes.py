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
#  HELPERS: SAFE RESULT EXTRACTION
# -------------------------------------------------------------
def extract_safe_result(result: dict):
    """
    Azure ML may return different formats:
    {"label": "..."} or {"sentiment": "..."} or {"prediction": "..."} or {"error": "..."}.
    This function handles EVERYTHING safely.
    """

    # If Azure returned an error
    if "error" in result:
        raise HTTPException(
            status_code=500,
            detail=f"Azure ML Error: {result.get('error')}"
        )

    label = (
        result.get("label") or
        result.get("sentiment") or
        result.get("prediction") or
        result.get("class") or
        "unknown"
    )

    score = (
        result.get("score") or
        result.get("prob") or
        result.get("confidence") or
        result.get("probability") or
        0.0
    )

    return label, float(score)


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

    # 🔥 SAFE extraction
    label, score = extract_safe_result(result)

    # Save to DB
    collection.insert_one({
        "user": username,
        "text": request.text,
        "label": label,
        "score": score
    })

    return {
        "text": request.text,
        "label": label,
        "score": score
    }


# -------------------------------------------------------------
#  HISTORY
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
        # 🔍 Skip duplicates
        if collection.find_one({"user": username, "text": text}):
            skipped_count += 1
            continue

        result = analyze_text(text)
        label, score = extract_safe_result(result)

        collection.insert_one({
            "user": username,
            "text": text,
            "label": label,
            "score": score
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
    result = collection.delete_one({"user": username, "text": text})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Text not found for this user"
        )

    return {"message": "Text deleted successfully", "text": text}
