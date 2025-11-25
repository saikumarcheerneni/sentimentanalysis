from fastapi import FastAPI
from app.routes import router as sentiment_router
from app.auth import router as auth_router 
app = FastAPI(
    title="Cloud Sentiment API",
    description="A RESTful API for sentiment analysis using Hugging Face + Azure Blob + JWT authentication.",
    version="2.0"
)

# Register routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(sentiment_router)

@app.get("/")
def home():
    return {"message": "Welcome to the Cloud Sentiment Analysis API"}
