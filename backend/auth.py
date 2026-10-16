"""
auth.py
-------
Authentication and session management for DSA Coach.
Features:
  - SQLite user storage with unique username and email constraints
  - Robust input validation (email format, password strength, username rules)
  - Direct bcrypt password hashing and verification
  - JWT access token generation and verification
  - Login by username OR email
"""

import os
import re
import time
import sqlite3
from datetime import datetime
from pathlib import Path

import jwt
import bcrypt

DB_PATH = Path(__file__).parent / "users.db"

# In production, set JWT_SECRET in your .env - this default is only for local dev.
SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-me-before-deploying")
ALGORITHM = "HS256"
TOKEN_EXPIRY_SECONDS = 60 * 60 * 24 * 7  # 7 days

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_-]{3,30}$")


class AuthError(Exception):
    """Custom exception raised for validation and authentication failures."""
    pass


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL COLLATE NOCASE,
            email TEXT UNIQUE NOT NULL COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    # Check if table was created in older version without email column
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    if "email" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
        conn.commit()

    conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    return conn


def hash_password(password: str) -> str:
    """Hash password using bcrypt with 12 salt rounds."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against bcrypt hash safely."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def validate_username(username: str) -> str:
    """Validate username length and character set."""
    if not username:
        raise AuthError("Username is required.")
    cleaned = username.strip().lower()
    if len(cleaned) < 3:
        raise AuthError("Username must be at least 3 characters long.")
    if len(cleaned) > 30:
        raise AuthError("Username must not exceed 30 characters.")
    if not USERNAME_REGEX.match(cleaned):
        raise AuthError("Username can only contain letters, numbers, underscores, and hyphens.")
    return cleaned


def validate_email(email: str) -> str:
    """Validate email format and length."""
    if not email:
        raise AuthError("Email address is required.")
    cleaned = email.strip().lower()
    if len(cleaned) > 255:
        raise AuthError("Email address is too long.")
    if not EMAIL_REGEX.match(cleaned):
        raise AuthError("Please provide a valid email address (e.g. user@example.com).")
    return cleaned


def validate_password_strength(password: str) -> None:
    """
    Validate password complexity:
      - Minimum 8 characters
      - Maximum 72 characters (bcrypt limit)
      - At least 1 uppercase letter
      - At least 1 lowercase letter
      - At least 1 digit
      - At least 1 special character
    """
    if not password:
        raise AuthError("Password is required.")
    if len(password) < 8:
        raise AuthError("Password must be at least 8 characters long.")
    if len(password) > 72:
        raise AuthError("Password cannot exceed 72 characters.")
    if not re.search(r"[a-z]", password):
        raise AuthError("Password must contain at least one lowercase letter.")
    if not re.search(r"[A-Z]", password):
        raise AuthError("Password must contain at least one uppercase letter.")
    if not re.search(r"\d", password):
        raise AuthError("Password must contain at least one number.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_+=\[\]\\/`~]", password):
        raise AuthError("Password must contain at least one special character (!@#$%^&* etc.).")


def create_user(username: str, email: str, password: str, display_name: str | None = None) -> dict:
    """
    Validate inputs, verify uniqueness of username and email, hash password,
    and persist user record.
    """
    valid_username = validate_username(username)
    valid_email = validate_email(email)
    validate_password_strength(password)

    display = display_name.strip() if display_name and display_name.strip() else valid_username

    conn = _conn()
    try:
        # Check unique username
        existing_user = conn.execute(
            "SELECT username FROM users WHERE LOWER(username) = ?", (valid_username,)
        ).fetchone()
        if existing_user:
            raise AuthError("A user with this username already exists.")

        # Check unique email
        existing_email = conn.execute(
            "SELECT email FROM users WHERE LOWER(email) = ?", (valid_email,)
        ).fetchone()
        if existing_email:
            raise AuthError("An account with this email address already exists.")

        hashed = hash_password(password)
        now = datetime.utcnow().isoformat()

        conn.execute(
            """
            INSERT INTO users (username, email, password_hash, display_name, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (valid_username, valid_email, hashed, display, now),
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "username": valid_username,
        "email": valid_email,
        "display_name": display,
    }


def verify_user(identifier: str, password: str) -> dict:
    """
    Verify credentials using either username or email as the identifier.
    Returns user dict on success, raises AuthError on failure.
    """
    if not identifier or not identifier.strip():
        raise AuthError("Username or email is required.")
    if not password:
        raise AuthError("Password is required.")

    clean_id = identifier.strip().lower()

    conn = _conn()
    try:
        row = conn.execute(
            """
            SELECT username, email, password_hash, display_name
            FROM users
            WHERE LOWER(username) = ? OR LOWER(email) = ?
            """,
            (clean_id, clean_id),
        ).fetchone()
    finally:
        conn.close()

    if not row or not verify_password(password, row[2]):
        raise AuthError("Invalid username/email or password.")

    return {
        "username": row[0],
        "email": row[1] or "",
        "display_name": row[3] or row[0],
    }


def get_user_by_username(username: str) -> dict | None:
    """Look up a user record by username."""
    if not username:
        return None
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT username, email, display_name FROM users WHERE LOWER(username) = ?",
            (username.strip().lower(),),
        ).fetchone()
    finally:
        conn.close()

    if not row:
        return None
    return {
        "username": row[0],
        "email": row[1] or "",
        "display_name": row[2] or row[0],
    }


def create_access_token(user_info: dict) -> str:
    """Generate signed JWT access token for the given user."""
    now = int(time.time())
    payload = {
        "sub": user_info["username"],
        "email": user_info.get("email", ""),
        "display_name": user_info.get("display_name", user_info["username"]),
        "iat": now,
        "exp": now + TOKEN_EXPIRY_SECONDS,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Decode and validate JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None
