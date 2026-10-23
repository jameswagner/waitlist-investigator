from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

load_dotenv()

from pydantic_ai.ui.ag_ui import AGUIAdapter

from .agent import agent

app = FastAPI(title="waitlist-investigator")


@app.post("/agent")
async def run_agent(request: Request) -> Response:
    return await AGUIAdapter.dispatch_request(request, agent=agent)


@app.get("/health")
async def health() -> dict:
    return {"ok": True}
