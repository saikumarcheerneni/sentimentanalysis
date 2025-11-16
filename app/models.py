from pydantic import BaseModel, EmailStr

class SentimentRequest(BaseModel):
    text: str

class SentimentResponse(BaseModel):
    text: str
    label: str
    score: float

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
