from fastapi import APIRouter

router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.get("/boom")
async def raise_test_error() -> None:
    """Специальный эндпоинт для проверки интеграции с GlitchTip."""
    raise RuntimeError("This is a test error for GlitchTip!")
