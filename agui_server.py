import json
import time
import uuid
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from langchain_core.messages import HumanMessage, AIMessage
from llm_config import SUPPORTED_LLMS, initialize_llm

APP_ROOT = "/Users/parag.kulkarni/ai-workspace/aws-infra-agent-bot"
UI_DIR = f"{APP_ROOT}/ui"

app = FastAPI(title="AWS Infra Agent Bot - AG-UI")
app.mount("/static", StaticFiles(directory=UI_DIR), name="static")

conversation_store: Dict[str, List] = {}
llm_cache: Dict[str, object] = {}


class RunRequest(BaseModel):
    message: str
    threadId: str
    provider: str
    model: Optional[str] = None
    credentialSource: Optional[str] = None


@app.get("/")
async def index():
    return FileResponse(f"{UI_DIR}/index.html")


@app.get("/api/models")
async def list_models():
    providers = []
    for key, config in SUPPORTED_LLMS.items():
        providers.append(
            {
                "key": key,
                "name": config["name"],
                "default_model": config["default_model"],
                "models": [config["default_model"]],
            }
        )
    return JSONResponse({"providers": providers})


def get_llm(provider: str, model: Optional[str], credential_source: Optional[str]):
    cache_key = f"{provider}:{model or ''}:{credential_source or 'auto'}"
    if cache_key in llm_cache:
        return llm_cache[cache_key]

    llm = initialize_llm(provider, model=model, preferred_source=credential_source)
    llm_cache[cache_key] = llm
    return llm


def sse_event(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


def now_ms() -> int:
    return int(time.time() * 1000)


@app.post("/api/run")
async def run_agent(payload: RunRequest):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    if payload.provider not in SUPPORTED_LLMS:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    run_id = str(uuid.uuid4())
    message_id = str(uuid.uuid4())
    thread_id = payload.threadId or str(uuid.uuid4())

    history = conversation_store.setdefault(thread_id, [])
    history.append(HumanMessage(content=payload.message))

    def stream():
        try:
            yield sse_event({
                "type": "RUN_STARTED",
                "runId": run_id,
                "threadId": thread_id,
                "timestamp": now_ms(),
            })

            yield sse_event({
                "type": "TEXT_MESSAGE_START",
                "messageId": message_id,
                "role": "assistant",
                "timestamp": now_ms(),
            })

            llm = get_llm(payload.provider, payload.model, payload.credentialSource)
            response = llm.invoke(history)
            response_text = response.content if response else ""
            if not response_text.strip():
                response_text = "No response generated."
            history.append(AIMessage(content=response_text))

            chunk_size = 60
            for idx in range(0, len(response_text), chunk_size):
                chunk = response_text[idx : idx + chunk_size]
                yield sse_event({
                    "type": "TEXT_MESSAGE_CONTENT",
                    "messageId": message_id,
                    "delta": chunk,
                    "timestamp": now_ms(),
                })

            yield sse_event({
                "type": "TEXT_MESSAGE_END",
                "messageId": message_id,
                "timestamp": now_ms(),
            })

            yield sse_event({
                "type": "RUN_FINISHED",
                "runId": run_id,
                "threadId": thread_id,
                "timestamp": now_ms(),
            })

        except Exception as exc:
            yield sse_event({
                "type": "RUN_ERROR",
                "runId": run_id,
                "threadId": thread_id,
                "message": str(exc),
                "timestamp": now_ms(),
            })

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("agui_server:app", host="0.0.0.0", port=8000, reload=True)
