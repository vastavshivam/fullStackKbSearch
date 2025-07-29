from fastapi import HTTPException
from jose.exceptions import ExpiredSignatureError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from utils.auth_utils import decode_jwt_token
from models.db_models import User
from database.database import get_db

async def get_file_id_from_token(token: str, refresh_token: str, refresh_url: str):
    try:
        payload = decode_jwt_token(token)
    except ExpiredSignatureError:
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Token expired. Provide refresh_token.")
        async with httpx.AsyncClient() as client:
            res = await client.post(refresh_url, json={"refresh_token": refresh_token})
            if res.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid refresh token")
            new_token = res.json()["token"]
            payload = decode_jwt_token(new_token)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    from database.database import async_session
    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == user_id))
        user = result.scalar_one_or_none()

    if not user or not user.file_id:
        raise HTTPException(status_code=404, detail="No file_id found for this user")

    return user_id, user.file_id
