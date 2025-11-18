from fastapi import APIRouter

router = APIRouter(tags=["utils"])


@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "message": "API is running"}
