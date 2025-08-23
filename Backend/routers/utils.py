from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pathlib import Path

router = APIRouter(tags=["utils"])


@router.get("/", response_class=HTMLResponse)
async def get_frontend():
    """Serve the frontend HTML file."""
    frontend_path = Path("Frontend/index.html")
    if frontend_path.exists():
        with open(frontend_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="<h1>Frontend not found</h1>")


@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "message": "API is running"}
