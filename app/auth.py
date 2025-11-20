# app/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import os

from app.models import UserCreate
from app.database import users_collection
from app.email_service import send_verification_email

router = APIRouter()

# -----------------------------
# CONFIG
# -----------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_key_please_change")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
EMAIL_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# -----------------------------
# HELPERS
# -----------------------------
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def authenticate_user(username: str, password: str):
    user = users_collection.find_one({"username": username})
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_email_token(email: str) -> str:
    to_encode = {
        "sub": email,
        "type": "verification",
        "exp": datetime.utcnow() + timedelta(hours=EMAIL_TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# -----------------------------
# ROUTES
# -----------------------------

@router.post("/register", status_code=201)
async def register(user: UserCreate):
    # Check if username OR email already exists
    existing = users_collection.find_one(
        {"$or": [{"username": user.username}, {"email": user.email}]}
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered",
        )

    hashed_password = get_password_hash(user.password)

    user_doc = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_password,
        "is_verified": False,
        "created_at": datetime.utcnow(),
    }

    users_collection.insert_one(user_doc)

    # Create email verification token
    token = create_email_token(user.email)
    send_verification_email(user.email, token)

    return {
        "message": "User registered successfully. Please check your email to verify your account."
    }


@router.get("/verify-email")
async def verify_email(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_type = payload.get("type")
        email = payload.get("sub")

        if token_type != "verification" or not email:
            raise HTTPException(status_code=400, detail="Invalid verification token")

        result = users_collection.update_one(
            {"email": email},
            {"$set": {"is_verified": True}},
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")

        return {"message": "Email verified successfully. You can now log in."}

    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

@router.post("/login")
async def login(user: UserLogin):
    db_user = await db_service.get_user_by_email(user.email)
    if not db_user or not bcrypt.checkpw(user.password.encode("utf-8"), db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    token = jwt_service.create_access_token({"email": user.email})
    return {"access_token": token, "token_type": "bearer"}
 

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    username = form_data.username
    password = form_data.password

    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )

    if not user.get("is_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your inbox.",
        )

    access_token = create_access_token({"sub": user["username"]})

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/verify")
async def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"message": f"Token valid for {username}"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
@router.put("/profile/update")
async def update_profile(update: UserUpdate, current_user=Depends(get_current_user)):
    data = {}
    if update.name: data["name"] = update.name
    if update.email: data["email"] = update.email
    if update.password:
        data["password"] = bcrypt.hashpw(update.password.encode("utf-8"), bcrypt.gensalt())
    await db_service.update_user(current_user["email"], data)
    return {"message": "Profile updated successfully."}


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = credentials.credentials
    await db_service.add_to_blacklist(token)
    return {"message": "Successfully logged out."}