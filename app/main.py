import logging
import os

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.routers import home, projects, chapters, narrative, export, settings, chat, locations, illustrations, analytics
from app.routers.deps import get_llm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
_UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AI Writer Lab starting (static=%s, uploads=%s)", _STATIC_DIR, _UPLOADS_DIR)
    try:
        from app.core.config import get_settings

        s = get_settings()
        logger.info(
            "Config: database_url=%s debug=%s openai_base_url=%s",
            s.database_url.split("///")[-1] if s.database_url else "",
            s.debug,
            (s.openai_base_url[:40] + "…") if s.openai_base_url and len(s.openai_base_url) > 40 else (s.openai_base_url or "(empty)"),
        )
    except Exception:
        logger.exception("Failed to log settings on startup")
    yield
    logger.info("AI Writer Lab shutting down")


app = FastAPI(title="AI Writer Lab", lifespan=lifespan)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon_ico():
    """Браузеры запрашивают /favicon.ico по умолчанию; отдаём SVG без 404."""
    return RedirectResponse(url="/static/favicon.svg", status_code=307)


if os.path.isdir(_STATIC_DIR):
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

app.include_router(home.router)
app.include_router(projects.router)
app.include_router(chapters.router)
app.include_router(narrative.router)
app.include_router(export.router)
app.include_router(settings.router)
app.include_router(chat.router)
app.include_router(locations.router)
app.include_router(illustrations.router)
app.include_router(analytics.router)

os.makedirs(_UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_UPLOADS_DIR), name="uploads")
