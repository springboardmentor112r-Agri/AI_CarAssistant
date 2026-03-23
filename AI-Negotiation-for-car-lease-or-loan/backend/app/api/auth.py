import hashlib
import logging
import uuid as _uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.core.database import get_db
from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.models.models import User, RefreshToken
from app.schemas.schemas import UserCreate, UserRead, Token
from app.api.deps import get_current_user
from app.services.password_reset_service import (
    create_reset_token,
    reset_password,
    check_token_valid,
)
from app.services.email_service import send_password_reset_email
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger("app.auth")

# ── Cookie name constant ──────────────────────────────────────────────────────
REFRESH_COOKIE = "refresh_token"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _set_refresh_cookie(response: Response, token: str) -> None:
    """Write the refresh token into an HTTP-only cookie."""
    kwargs: dict = dict(
        key=REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.JWT_REFRESH_EXPIRE_DAYS * 24 * 60 * 60,
        path="/auth",
    )
    if settings.COOKIE_DOMAIN:
        kwargs["domain"] = settings.COOKIE_DOMAIN
    response.set_cookie(**kwargs)


def _clear_refresh_cookie(response: Response) -> None:
    kwargs: dict = dict(key=REFRESH_COOKIE, path="/auth")
    if settings.COOKIE_DOMAIN:
        kwargs["domain"] = settings.COOKIE_DOMAIN
    response.delete_cookie(**kwargs)


async def _store_refresh_token(
    db: AsyncSession, user_id: UUID, token: str
) -> None:
    """Persist SHA-256 hash of the refresh token in the database."""
    db_token = RefreshToken(
        user_id=user_id,
        token_hash=_hash(token),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
        revoked=False,
    )
    db.add(db_token)
    await db.commit()


async def _revoke_refresh_token(db: AsyncSession, token: str) -> None:
    """Mark a refresh token as revoked (token rotation / logout)."""
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == _hash(token))
    )
    db_token = result.scalar_one_or_none()
    if db_token:
        db_token.revoked = True
        await db.commit()


async def _purge_expired_tokens(db: AsyncSession, user_id: UUID) -> None:
    """House-keeping: delete expired tokens for a given user."""
    await db.execute(
        delete(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.expires_at < datetime.now(timezone.utc),
        )
    )
    await db.commit()


# ── Registration ──────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    email = data.email.strip().lower()
    try:
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            logger.info("register rejected: duplicate email=%s", email)
            raise HTTPException(status_code=400, detail="Email already registered")

        user = User(
            email=email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info("register success: user_id=%s email=%s", user.user_id, email)
        return user
    except IntegrityError:
        await db.rollback()
        logger.exception("register integrity error: email=%s", email)
        raise HTTPException(status_code=400, detail="Email already registered")
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("register database error: email=%s", email)
        raise HTTPException(status_code=500, detail="Database error during registration")


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user.
    • Returns short-lived access token in the JSON body.
    • Sets long-lived refresh token in an HTTP-only cookie.
    """
    email = form.username.strip().lower()
    try:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(form.password, user.hashed_password):
            logger.info("login rejected: invalid credentials email=%s", email)
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not user.is_active:
            logger.info("login rejected: inactive user_id=%s", user.user_id)
            raise HTTPException(status_code=403, detail="Account is inactive")

        jti = str(_uuid.uuid4())
        access_token = create_access_token({"sub": str(user.user_id), "jti": jti})
        refresh_token = create_refresh_token(
            {"sub": str(user.user_id), "jti": str(_uuid.uuid4())}
        )

        # Persist refresh token hash & set cookie
        await _purge_expired_tokens(db, user.user_id)
        await _store_refresh_token(db, user.user_id, refresh_token)
        _set_refresh_cookie(response, refresh_token)

        logger.info("login success: user_id=%s email=%s", user.user_id, email)
        return {"access_token": access_token, "token_type": "bearer", "user": user}
    except HTTPException:
        raise
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("login database error: email=%s", email)
        raise HTTPException(status_code=500, detail="Database error during login")


# ── Refresh ───────────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=Token)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Issue a new access token using the refresh token cookie.
    Implements full token rotation: old refresh token is revoked and
    a brand-new one is issued. Replay of a revoked token returns 401.
    """
    refresh_token = request.cookies.get(REFRESH_COOKIE)
    if not refresh_token:
        logger.info("refresh rejected: no refresh cookie")
        raise HTTPException(status_code=401, detail="No refresh token")

    # 1. Verify JWT signature and expiry
    payload = decode_refresh_token(refresh_token)

    # 2. Check DB — token must exist, not revoked, not expired
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == _hash(refresh_token),
            RefreshToken.revoked == False,
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
    )
    db_token = result.scalar_one_or_none()
    if not db_token:
        # Possible token reuse attack — clear the cookie too
        _clear_refresh_cookie(response)
        logger.info("refresh rejected: token missing/revoked/expired")
        raise HTTPException(
            status_code=401, detail="Refresh token invalid, expired or already used"
        )

    # 3. Revoke the consumed token (rotation)
    db_token.revoked = True

    # 4. Load user
    user_id = payload.get("sub")
    user_result = await db.execute(
        select(User).where(
            User.user_id == UUID(user_id),
            User.is_active == True,
        )
    )
    user = user_result.scalar_one_or_none()
    if not user:
        await db.commit()
        _clear_refresh_cookie(response)
        logger.info("refresh rejected: user missing or inactive")
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # 5. Issue new token pair
    new_access_token = create_access_token(
        {"sub": str(user.user_id), "jti": str(_uuid.uuid4())}
    )
    new_refresh_token = create_refresh_token(
        {"sub": str(user.user_id), "jti": str(_uuid.uuid4())}
    )

    # Persist new refresh token
    new_db_token = RefreshToken(
        user_id=user.user_id,
        token_hash=_hash(new_refresh_token),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
        revoked=False,
    )
    db.add(new_db_token)
    await db.commit()

    _set_refresh_cookie(response, new_refresh_token)
    logger.info("refresh success: user_id=%s", user.user_id)

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "user": user,
    }


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Revoke the refresh token stored in the cookie and clear it.
    The short-lived access token expires on its own.
    """
    refresh_token = request.cookies.get(REFRESH_COOKIE)
    if refresh_token:
        await _revoke_refresh_token(db, refresh_token)

    _clear_refresh_cookie(response)
    return {"message": "Logged out"}


# ── Current user ──────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


# ── Password reset ────────────────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class CheckTokenRequest(BaseModel):
    token: str


@router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Request password reset email.
    Always returns the same response — prevents user enumeration.
    """
    email = body.email.strip().lower()
    if "@" not in email or "." not in email:
        return {
            "message": "If an account exists with this email, a reset link has been sent."
        }

    plain_token, user_email = await create_reset_token(db, email)
    if plain_token and user_email:
        background_tasks.add_task(send_password_reset_email, user_email, plain_token)

    return {
        "message": "If an account exists with this email, a reset link has been sent."
    }


@router.post("/check-reset-token")
async def check_reset_token(
    body: CheckTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    is_valid = await check_token_valid(db, body.token)
    if not is_valid:
        raise HTTPException(
            400,
            "This reset link has expired or already been used. Please request a new one.",
        )
    return {"valid": True}


@router.post("/reset-password")
async def reset_password_endpoint(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    if len(body.new_password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters.")
    if len(body.new_password) > 128:
        raise HTTPException(400, "Password too long.")

    success = await reset_password(db, body.token, body.new_password)
    if not success:
        raise HTTPException(
            400,
            "This reset link has expired or already been used. Please request a new one.",
        )

    return {"message": "Password reset successfully."}
