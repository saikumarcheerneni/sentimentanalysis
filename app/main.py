from fastapi import FastAPI
import time
from fastapi import Request
from app.database import performance_collection
from datetime import datetime
from app.routes import router as sentiment_router
from app.extraction import router as extraction_router
from app.auth import router as auth_router 
app = FastAPI(
    title="Cloud Sentiment API",    
    description="A RESTful API for sentiment analysis using Hugging Face + Azure Blob + JWT authentication.",
    version="2.0"
)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(extraction_router, tags=["Review Extraction"])
app.include_router(sentiment_router)

@app.get("/")
def home():
    return {"message": "Welcome to the Cloud Sentiment Analysis API"}

@app.middleware("http")
async def measure_request_time(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    end = time.time()

    performance_collection.insert_one({
        "type": "backend_response",
        "path": request.url.path,
        "duration_ms": round((end - start) * 1000, 3),
        "timestamp": datetime.utcnow()
    })

    return response