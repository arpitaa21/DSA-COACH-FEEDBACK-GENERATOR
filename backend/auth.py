"""
auth.py
-------
Minimal username/password auth so daily-practice streaks can be tracked correctly
per real user instead of a shared "guest" bucket.

Deliberately simple: SQLite user table + bcrypt password hashing + JWT session
tokens. Good enough for a class project / small deployment; swap for a managed
auth provider before this ever sees real user data.
"""

import os
import time
import sqlite3
from datetime import datetime
from pathlib import Path

import jwt
from passlib.context import CryptContext

DB_PATH = Path(__file__).parent / "users.db"

# In production, set JWT_SECRET in your .env - this default is only for local dev.
SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-me-before-deploying")
ALGORITHM = "HS256"
TOKEN_EXPIRY_SECONDS = 60 * 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    return conn


class AuthError(Exception):
    pass


def create_user(username: str, password: str, display_name: str | None = None) -> dict:
    username = username.strip().lower()
    if len(username) < 3:
        raise AuthError("Username must be at least 3 characters.")
    if len(password) < 6:
        raise AuthError("Password must be at least 6 characters.")

    conn = _conn()
    existing = conn.execute("SELECT username FROM users WHERE username = ?", (username,)).fetchone()
    if existing:
        conn.close()
        raise AuthError("That username is already taken.")

    conn.execute(
        "INSERT INTO users (username, password_hash, display_name, created_at) VALUES (?, ?, ?, ?)",
        (username, pwd_context.hash(password), display_name or username, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    return {"username": username, "display_name": display_name or username}


def verify_user(username: str, password: str) -> dict:
    username = username.strip().lower()
    conn = _conn()
    row = conn.execute(
        "SELECT password_hash, display_name FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()

    if not row or not pwd_context.verify(password, row[0]):
        raise AuthError("Incorrect username or password.")

    return {"username": username, "display_name": row[1]}


def create_access_token(username: str) -> str:
    payload = {"sub": username, "exp": int(time.time()) + TOKEN_EXPIRY_SECONDS}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None
