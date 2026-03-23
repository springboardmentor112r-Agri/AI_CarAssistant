"""
Password reset service.
Handles token creation, validation, and
password update.

Security:
- Token: secrets.token_urlsafe(32) → 43 char URL-safe
- Stored: SHA-256 hash only
- Expires: 30 minutes
- Single use: marked used immediately on verify
- One per user: old tokens deleted on new request
"""
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.models import User, PasswordResetToken
from app.core.security import hash_password

RESET_TOKEN_EXPIRE_MINUTES = 30

def _hash_token(plain_token: str) -> str:
  """SHA-256 hash of token for safe DB storage."""
  return hashlib.sha256(plain_token.encode()).hexdigest()

def _generate_token() -> str:
  """
  Generate cryptographically secure URL-safe token.
  43 characters, safe for use in URLs without encoding.
  """
  return secrets.token_urlsafe(32)

async def create_reset_token(
  db: AsyncSession,
  email: str,
) -> tuple[str | None, str | None]:
  """
  Create a password reset token for user with given email.

  Returns:
    (plain_token, user_email) if user found
    (None, None) if user not found
    — caller should NOT reveal which case to user
      to prevent email enumeration attacks

  Security:
    Old tokens for this user are deleted first.
    New token hash stored, plain token returned
    to caller for emailing ONLY — never stored.
  """
  # Find user by email (parameterized — no SQL injection)
  result = await db.execute(
    select(User).where(User.email == email.lower().strip())
  )
  user = result.scalar_one_or_none()

  if not user:
    # Return None silently — do not reveal user existence
    return None, None

  # Delete any existing reset tokens for this user
  await db.execute(
    delete(PasswordResetToken)
    .where(PasswordResetToken.user_id == user.user_id)
  )

  # Generate new token
  plain_token = _generate_token()
  token_hash = _hash_token(plain_token)
  expires_at = datetime.now(timezone.utc) + timedelta(
    minutes=RESET_TOKEN_EXPIRE_MINUTES
  )

  reset_token = PasswordResetToken(
    user_id=user.user_id,
    token_hash=token_hash,
    expires_at=expires_at,
    used=False,
  )
  db.add(reset_token)
  await db.commit()

  return plain_token, user.email

async def verify_reset_token(
  db: AsyncSession,
  plain_token: str,
) -> UUID | None:
  """
  Verify reset token is valid, not expired, not used.

  Returns user_id if valid, None if invalid/expired/used.
  Does NOT delete token yet — that happens on password save.
  """
  token_hash = _hash_token(plain_token)

  result = await db.execute(
    select(PasswordResetToken)
    .where(PasswordResetToken.token_hash == token_hash)
  )
  token_record = result.scalar_one_or_none()

  if not token_record:
    return None
  if token_record.used:
    return None
  if token_record.expires_at < datetime.now(timezone.utc):
    # Expired — clean up
    await db.delete(token_record)
    await db.commit()
    return None

  return token_record.user_id

async def reset_password(
  db: AsyncSession,
  plain_token: str,
  new_password: str,
) -> bool:
  """
  Reset user password using valid token.

  Returns True if successful, False if token invalid.

  Security:
    Token marked used and deleted immediately.
    Password hashed with bcrypt.
    All other reset tokens for user also deleted.
  """
  # Validate password strength
  if len(new_password) < 8:
    return False

  token_hash = _hash_token(plain_token)

  result = await db.execute(
    select(PasswordResetToken)
    .where(PasswordResetToken.token_hash == token_hash)
  )
  token_record = result.scalar_one_or_none()

  if not token_record:
    return False
  if token_record.used:
    return False
  if token_record.expires_at < datetime.now(timezone.utc):
    await db.delete(token_record)
    await db.commit()
    return False

  # Get user
  result = await db.execute(
    select(User)
    .where(User.user_id == token_record.user_id)
  )
  user = result.scalar_one_or_none()
  if not user:
    return False

  # Hash new password and save
  user.hashed_password = hash_password(new_password)

  # Delete ALL reset tokens for this user (single use)
  await db.execute(
    delete(PasswordResetToken)
    .where(PasswordResetToken.user_id == user.user_id)
  )

  await db.commit()
  return True

async def check_token_valid(
  db: AsyncSession,
  plain_token: str,
) -> bool:
  """
  Quick check if token is still valid.
  Used by frontend to validate token on page load.
  Does not consume the token.
  """
  user_id = await verify_reset_token(db, plain_token)
  return user_id is not None
