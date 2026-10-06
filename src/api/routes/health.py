from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    # Проверяем, что БД отвечает
    await session.execute(text("SELECT 1"))
    return {"status": "ok"}
