"""Exercises the real agent and tool wiring with a scripted model (not a live LLM)."""
import pytest
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import FunctionModel
from pydantic_core import to_jsonable_python

from app.agent import agent


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_agent_calls_engagement_tool(db):
    def script(messages, info):
        if any(isinstance(p, ToolReturnPart) for m in messages for p in m.parts):
            return ModelResponse(parts=[TextPart("done")])
        args = {"practice_id": "a", "start_date": "2025-03-01", "end_date": "2025-03-31"}
        return ModelResponse(parts=[ToolCallPart("get_offer_engagement", args)])

    with agent.override(model=FunctionModel(script)):
        res = await agent.run("go")
    ret = next(p for m in res.all_messages() for p in m.parts if isinstance(p, ToolReturnPart))
    payload = to_jsonable_python(ret.content)
    assert payload["status"] == "ok" and payload["rows"][0]["sent"] == 3


def test_ag_ui_endpoint_streams_tool_result(db):
    import json

    from pydantic_ai.models.function import DeltaToolCall
    from starlette.testclient import TestClient

    from app.main import app

    async def stream(messages, info):
        if any(isinstance(p, ToolReturnPart) for m in messages for p in m.parts):
            yield "done"
            return
        args = {"practice_id": "a", "start_date": "2025-03-01", "end_date": "2025-03-31"}
        yield {0: DeltaToolCall(name="get_offer_engagement", json_args=json.dumps(args))}

    body = {"threadId": "t", "runId": "r", "state": {}, "tools": [], "context": [],
            "forwardedProps": {}, "messages": [{"id": "1", "role": "user", "content": "hi"}]}
    with agent.override(model=FunctionModel(stream_function=stream)):
        r = TestClient(app).post("/agent", json=body, headers={"accept": "text/event-stream"})
    events = [json.loads(line[6:]) for line in r.text.splitlines() if line.startswith("data: ")]
    result = next(e for e in events if e["type"] == "TOOL_CALL_RESULT")
    assert json.loads(result["content"])["rows"][0]["sent"] == 3
