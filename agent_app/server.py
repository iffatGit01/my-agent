"""FastAPI server: serves the chat page and a /chat endpoint."""

from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from .agent import build_agent

load_dotenv()

STATIC_DIR = Path(__file__).parent / "static"


class ChatRequest(BaseModel):
    message: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        app.state.agent = await build_agent(stack)
        yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        result = await app.state.agent.run(req.message)
        return {"reply": result.text}
    except Exception as exc:  # surface a friendly error to the UI
        return JSONResponse(status_code=500, content={"error": str(exc)})
