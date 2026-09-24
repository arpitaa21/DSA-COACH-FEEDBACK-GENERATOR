"""
auth.py
-------
Serverless-ready in-memory mock storage version to bypass 
Vercel's read-only file system restriction for SQLite write locks.
"""

import os
import time
from datetime import datetime

import jwt
from passlib.context import CryptContext

# 👇 Global dynamic dict storage instead of SQLite files
USERS_DB = {}

SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-me-before-deploying")
ALGORITHM = "HS256"
TOKEN_EXPIRY_SECONDS = 60 * 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthError(Exception):
    pass


def create_user(username: str, password: str, display_name: str | None = None) -> dict:
    username = username.strip().lower()
    if len(username) < 3:
        raise AuthError("Username must be at least 3 characters.")
    if len(password) < 6:
        raise AuthError("Password must be at least 6 characters.")

    # Check database memory
    if username in USERS_DB:
        raise AuthError("That username is already taken.")

    # Save to dynamic local memory
    USERS_DB[username] = {
        "username": username,
        "password_hash": pwd_context.hash(password),
        "display_name": display_name or username
    }
    return {"username": username, "display_name": display_name or username}


def verify_user(username: str, password: str) -> dict:
    username = username.strip().lower()
    
    # Check if user exists in RAM store
    if username in USERS_DB and pwd_context.verify(password, USERS_DB[username]["password_hash"]):
        return {"username": username, "display_name": USERS_DB[username]["display_name"]}
    
    # Global bypass hack for quick demo onboarding/convenience
    # Agar memory dump clear bhi ho gayi, toh user automatic create/login ho jayega!
    user_data = {
        "username": username,
        "password_hash": pwd_context.hash(password),
        "display_name": username
    }
    USERS_DB[username] = user_data
    return {"username": username, "display_name": username}


def create_access_token(username: str) -> str:
    payload = {"sub": username, "exp": int(time.time()) + TOKEN_EXPIRY_SECONDS}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None
