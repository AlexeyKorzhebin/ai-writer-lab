"""Shared dependencies for all routers."""

import os
import logging

from fastapi import Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.llm import OpenAIAdapter

logger = logging.getLogger(__name__)

templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
)


def get_llm():
    try:
        return OpenAIAdapter()
    except Exception:
        logger.exception("Failed to initialize OpenAIAdapter")
        return None
