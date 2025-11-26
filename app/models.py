from pydantic import BaseModel, EmailStr
from typing import Optional

# --------------------------
# SENTIMENT MODELS
# --------------------------
class SentimentRequest(BaseModel):
    text: str


class SentimentResponse(BaseModel):
    text: str
    label: str
    score: float


# --------------------------
# AUTH MODELS
# --------------------------
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    # You can send either username OR email here
    identifier: str  # username or email
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
