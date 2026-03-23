from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.database import get_db
from app.core.security import decode_token
from app.models.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(401, "Invalid token payload")
    result = await db.execute(
        select(User).where(
            User.user_id == UUID(user_id),
            User.is_active == True
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(401, "User not found or inactive")
    return user
