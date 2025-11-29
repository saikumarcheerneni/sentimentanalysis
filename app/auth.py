from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import os

from app.models import UserCreate, UserLogin, UserUpdate
from app.database import users_collection
from app.email_service import send_verification_email, send_goodbye_email
from app.blob_service import delete_user_folder

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_key_change_me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
EMAIL_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
bearer_scheme = HTTPBearer()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def authenticate_user(identifier: str, password: str):
    """identifier can be username OR email"""
    user = users_collection.find_one(
        {"$or": [{"username": identifier}, {"email": identifier}]}
    )

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


def create_email_token(email: str):
    return jwt.encode(
        {
            "sub": email,
            "type": "verification",
            "exp": datetime.utcnow() + timedelta(hours=EMAIL_TOKEN_EXPIRE_HOURS),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validates the JWT and returns the user from DB."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        if username is None:
            raise HTTPException(401, "Invalid token")

    except JWTError:
        raise HTTPException(401, "Invalid token")

    user = users_collection.find_one({"username": username})

    if not user:
        raise HTTPException(401, "User not found")

    return user


@router.post("/register", status_code=201)
async def register(user: UserCreate):
    existing = users_collection.find_one(
        {"$or": [{"username": user.username}, {"email": user.email}]}
    )

    if existing:
        raise HTTPException(400, "Username or Email already registered")

    hashed_password = get_password_hash(user.password)

    users_collection.insert_one(
        {
            "username": user.username,
            "email": user.email,
            "hashed_password": hashed_password,
            "is_verified": False,
            "created_at": datetime.utcnow(),
        }
    )

    token = create_email_token(user.email)
    send_verification_email(user.email, token)

    return {
        "message": "User registered successfully. Please verify email.",
        "verification_token": token,
    }


@router.get("/verify", include_in_schema=False)
async def verify_email(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != "verification":
            raise HTTPException(400, "Invalid verification token")

        email = payload.get("sub")

        if not email:
            raise HTTPException(400, "Invalid email token")

        result = users_collection.update_one(
            {"email": email},
            {"$set": {"is_verified": True}},
        )

        if result.matched_count == 0:
            raise HTTPException(404, "User not found")

        return {"message": "Email verified. You may now log in."}

    except JWTError:
        raise HTTPException(400, "Invalid or expired token")


@router.post("/manual")
async def verify_email_manual(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != "verification":
            raise HTTPException(400, "Invalid verification token")

        email = payload.get("sub")

        if not email:
            raise HTTPException(400, "Invalid email token")

        result = users_collection.update_one(
            {"email": email},
            {"$set": {"is_verified": True}},
        )

        if result.matched_count == 0:
            raise HTTPException(404, "User not found")

        return {
            "message": "Email verified manually.",
            "email": email,
        }

    except JWTError:
        raise HTTPException(400, "Invalid or expired token")


@router.post("/token")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    # form.username = username OR email
    user = authenticate_user(form.username, form.password)

    if not user:
        raise HTTPException(400, "Incorrect username or password")

    if not user.get("is_verified"):
        raise HTTPException(403, "Email not verified")

    token = create_access_token({"sub": user["username"]})

    return {"access_token": token, "token_type": "bearer"}


@router.get("/verify")
async def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"valid": True, "user": payload.get("sub")}
    except:
        raise HTTPException(401, "Invalid token")


@router.put("/update")
async def update_profile(update: UserUpdate, current_user=Depends(get_current_user)):
    data = {}

    if update.name:
        data["name"] = update.name

    if update.email:
        # ensure email is unique
        exists = users_collection.find_one({"email": update.email})
        if exists and exists["username"] != current_user["username"]:
            raise HTTPException(400, "Email already in use")

        data["email"] = update.email

    if update.password:
        data["hashed_password"] = get_password_hash(update.password)

    if data:
        users_collection.update_one(
            {"username": current_user["username"]},
            {"$set": data},
        )

    return {"message": "Profile updated successfully"}


@router.post("/logout")
async def logout(_: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    return {"message": "Logout successful (client must delete token)"}


@router.delete("/delete")
async def delete_account(current_user=Depends(get_current_user)):
    username = current_user["username"]
    email = current_user["email"]

    result = users_collection.delete_one({"username": username})

    if result.deleted_count == 0:
        raise HTTPException(404, "User not found")

    delete_user_folder(username)
    send_goodbye_email(email)

    return {
        "message": "Account and all files deleted successfully.",
        "status": "success",
    }
