from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import os

router = APIRouter()

# -----------------------------
# CONFIG
# -----------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_key_please_change")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Use pbkdf2_sha256 only (Azure-safe)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# -----------------------------
# STATIC USER (NO HASHING AT STARTUP)
# Generate pbkdf2 hash using:
# from passlib.context import CryptContext
# pwd = CryptContext(schemes=["pbkdf2_sha256"])
# print(pwd.hash("1234"))
# -----------------------------
fake_users_db = {
    "saiku": {
        "username": "saiku",
        "hashed_password": "$pbkdf2-sha256$29000$eP0TQnkZR1PFVTV1Wt9eZg$u/9gIh9CUU3z2J8WxSE9Dq1BwCy2cxEER/62g/7QM6o"
    }
}

# -----------------------------
# HELPERS
# -----------------------------
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# -----------------------------
# ROUTES
# -----------------------------
@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password"
        )
    token = create_access_token({"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}

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
