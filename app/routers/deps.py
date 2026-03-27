"""Shared dependencies for all routers."""

import os
import logging

from fastapi import Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.llm import OpenAIAdapter
from app.services import llm_providers as lp

logger = logging.getLogger(__name__)

templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
)


async def get_llm(db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.settings_repository import SettingsRepository

    try:
        repo = SettingsRepository(db)
        base_url = (await repo.get("base_url", "") or "").strip()
        if not base_url:
            return None
        api_key = await repo.get("api_key", "") or ""
        model = (await repo.get("model", "") or "").strip() or None
        extra_raw = await repo.get("llm_extra_headers", "") or ""
        extra = lp.parse_extra_headers_dict(extra_raw)
        return OpenAIAdapter(
            base_url=base_url,
            api_key=api_key,
            model=model,
            extra_headers=extra,
        )
    except Exception:
        logger.exception("Failed to initialize OpenAIAdapter")
        return None
