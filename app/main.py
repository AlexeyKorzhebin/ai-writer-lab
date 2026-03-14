from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import logging

from app.core.llm import OpenAIAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Writer Lab")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# ---------- LLM Adapter ----------
llm_adapter = None

try:
    llm_adapter = OpenAIAdapter()
    logger.info("LLM adapter initialized")
except Exception as e:
    logger.warning(f"LLM adapter not initialized: {e}")


# ---------- Models ----------
class GenerateRequest(BaseModel):
    prompt: str
    temperature: float = 0.7
    max_tokens: int = 512


class GenerateResponse(BaseModel):
    text: str


# ---------- Routes ----------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    logger.info("Home page requested")
    return templates.TemplateResponse(
        "home.html",
        {"request": request}
    )


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    if not llm_adapter:
        return {"text": "LLM is not configured. Set LLM_BASE_URL."}

    text = await llm_adapter.generate(
        prompt=request.prompt,
    )

    return {"text": text}
