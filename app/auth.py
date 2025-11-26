# # app/auth.py
# from fastapi import APIRouter, Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from jose import JWTError, jwt
# from passlib.context import CryptContext
# from datetime import datetime, timedelta
# from typing import Optional
# import os
# from app.models import UserCreate, UserLogin, UserUpdate
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# import bcrypt

# bearer_scheme = HTTPBearer()

# from app.models import UserCreate
# from app.database import users_collection
# from app.email_service import send_verification_email

# router = APIRouter()

# # -----------------------------
# # CONFIG
# # -----------------------------
# SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_key_please_change")
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30
# EMAIL_TOKEN_EXPIRE_HOURS = 24

# pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# # -----------------------------
# # HELPERS
# # -----------------------------
# def verify_password(plain_password, hashed_password):
#     return pwd_context.verify(plain_password, hashed_password)


# def get_password_hash(password: str) -> str:
#     return pwd_context.hash(password)


# def authenticate_user(username: str, password: str):
#     user = users_collection.find_one({"username": username})
#     if not user:
#         return None
#     if not verify_password(password, user["hashed_password"]):
#         return None
#     return user


# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + (
#         expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     )
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# def create_email_token(email: str) -> str:
#     to_encode = {
#         "sub": email,
#         "type": "verification",
#         "exp": datetime.utcnow() + timedelta(hours=EMAIL_TOKEN_EXPIRE_HOURS),
#     }
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# # -----------------------------
# # ROUTES
# # -----------------------------

# @router.post("/register", status_code=201)
# async def register(user: UserCreate):
#     # Check if username OR email already exists
#     existing = users_collection.find_one(
#         {"$or": [{"username": user.username}, {"email": user.email}]}
#     )
#     if existing:
#         raise HTTPException(
#             status_code=400,
#             detail="Username or email already registered",
#         )

#     hashed_password = get_password_hash(user.password)

#     user_doc = {
#         "username": user.username,
#         "email": user.email,
#         "hashed_password": hashed_password,
#         "is_verified": False,
#         "created_at": datetime.utcnow(),
#     }

#     users_collection.insert_one(user_doc)

#     # Create email verification token
#     token = create_email_token(user.email)
#     send_verification_email(user.email, token)

#     return {
#         "message": "User registered successfully. Please check your email to verify your account."
#     }


# @router.get("/verify-email")
# async def verify_email(token: str):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         token_type = payload.get("type")
#         email = payload.get("sub")

#         if token_type != "verification" or not email:
#             raise HTTPException(status_code=400, detail="Invalid verification token")

#         result = users_collection.update_one(
#             {"email": email},
#             {"$set": {"is_verified": True}},
#         )

#         if result.matched_count == 0:
#             raise HTTPException(status_code=404, detail="User not found")

#         return {"message": "Email verified successfully. You can now log in."}

#     except JWTError:
#         raise HTTPException(status_code=400, detail="Invalid or expired verification token")

# @router.post("/login")
# async def login(user: UserLogin):
#     db_user = await db_service.get_user_by_email(user.email)
#     if not db_user or not bcrypt.checkpw(user.password.encode("utf-8"), db_user["password"]):
#         raise HTTPException(status_code=401, detail="Invalid credentials.")
#     token = jwt_service.create_access_token({"email": user.email})
#     return {"access_token": token, "token_type": "bearer"}
 

# @router.post("/token")
# async def login(form_data: OAuth2PasswordRequestForm = Depends()):
#     username = form_data.username
#     password = form_data.password

#     user = authenticate_user(username, password)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Incorrect username or password",
#         )

#     if not user.get("is_verified", False):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Email not verified. Please check your inbox.",
#         )

#     access_token = create_access_token({"sub": user["username"]})

#     return {"access_token": access_token, "token_type": "bearer"}


# @router.get("/verify")
# async def verify_token(token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username = payload.get("sub")
#         if username is None:
#             raise HTTPException(status_code=401, detail="Invalid token")
#         return {"message": f"Token valid for {username}"}
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid token")
    
# @router.put("/profile/update")
# async def update_profile(update: UserUpdate, current_user=Depends(get_current_user)):
#     data = {}
#     if update.name: data["name"] = update.name
#     if update.email: data["email"] = update.email
#     if update.password:
#         data["password"] = bcrypt.hashpw(update.password.encode("utf-8"), bcrypt.gensalt())
#     await db_service.update_user(current_user["email"], data)
#     return {"message": "Profile updated successfully."}


# @router.post("/logout")
# async def logout(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
#     if not credentials:
#         raise HTTPException(status_code=401, detail="Not authenticated")
#     token = credentials.credentials
#     await db_service.add_to_blacklist(token)
#     return {"message": "Successfully logged out."}

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
from app.email_service import send_verification_email
from app.azure_blob import delete_user_folder
from app.email_service import send_goodbye_email


router = APIRouter()

# -----------------------------
# CONFIG
# -----------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_key_change_me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
EMAIL_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# OAuth2 login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Simple bearer scheme for logout
bearer_scheme = HTTPBearer()


# -----------------------------
# PASSWORD + TOKEN HELPERS
# -----------------------------
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


# -----------------------------
# CURRENT USER DEPENDENCY
# -----------------------------
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


# -----------------------------
# ROUTES
# -----------------------------
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
    "verification_token": token
}

    


@router.get("/verify-email", include_in_schema=False)
async def verify_email(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "verification":
            raise HTTPException(400, "Invalid verification token")

        email = payload.get("sub")
        if not email:
            raise HTTPException(400, "Invalid email token")

        result = users_collection.update_one(
            {"email": email}, {"$set": {"is_verified": True}}
        )

        if result.matched_count == 0:
            raise HTTPException(404, "User not found")

        return {"message": "Email verified. You may now log in."}

    except JWTError:
        raise HTTPException(400, "Invalid or expired token")

@router.post("/verify-email/manual")
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
            {"$set": {"is_verified": True}}
        )

        if result.matched_count == 0:
            raise HTTPException(404, "User not found")

        return {
            "message": "Email verified manually.",
            "email": email
        }

    except JWTError:
        raise HTTPException(400, "Invalid or expired token")

# -----------------------------
# MAIN LOGIN ENDPOINT
# -----------------------------
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


# -----------------------------
# TOKEN VERIFICATION
# -----------------------------
@router.get("/verify")
async def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"valid": True, "user": payload.get("sub")}
    except:
        raise HTTPException(401, "Invalid token")


# -----------------------------
# PROFILE UPDATE
# -----------------------------
@router.put("/profile/update")
async def update_profile(update: UserUpdate, current_user=Depends(get_current_user)):
    data = {}

    if update.name:
        data["name"] = update.name

    if update.email:
        # ensure unique email
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


# -----------------------------
# LOGOUT (NO BLACKLIST – OPTIONAL)
# -----------------------------
@router.post("/logout")
async def logout(_: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    return {"message": "Logout successful (client must delete token)"}




@router.delete("/delete-account")
async def delete_account(current_user=Depends(get_current_user)):
    username = current_user["username"]
    email = current_user["email"]

    # 1. Delete user record from DB
    result = users_collection.delete_one({"username": username})

    if result.deleted_count == 0:
        raise HTTPException(404, "User not found")

    # 2. Delete files from Azure Blob Storage
    delete_user_folder(username)

    # 3. Send goodbye email
    send_goodbye_email(email)

    return {
        "message": "Account and all files deleted successfully.",
        "status": "success"
    }

