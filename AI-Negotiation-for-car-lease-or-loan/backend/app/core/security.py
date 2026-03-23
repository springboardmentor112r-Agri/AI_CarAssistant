import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from app.core.config import settings


def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt(rounds=10)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def _refresh_secret() -> str:
    """Use dedicated refresh secret if set, else fall back to JWT_SECRET."""
    return settings.JWT_REFRESH_SECRET or settings.JWT_SECRET


# ── Access token ──────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ── Refresh token ─────────────────────────────────────────────────────────────

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_EXPIRE_DAYS
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, _refresh_secret(), algorithm="HS256")


def decode_refresh_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, _refresh_secret(), algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except JWTError:
        raise HTTPException(
            status_code=401, detail="Invalid or expired refresh token"
        )
