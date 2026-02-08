import json
import time
import uuid
from typing import Dict, List, Optional
import warnings
import os
import logging
import sys
from datetime import datetime

# Suppress urllib3 NotOpenSSLWarning when the system ssl is LibreSSL.
# This is a benign warning on macOS with system LibreSSL and doesn't affect runtime.
try:
    from urllib3.exceptions import NotOpenSSLWarning

    warnings.filterwarnings("ignore", category=NotOpenSSLWarning)
except Exception:
    # If urllib3 isn't available yet or the exception class isn't present,
    # skip silencing the warning to avoid import errors.
    pass

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
 

from langchain_core.messages import HumanMessage, AIMessage
from llm_config import SUPPORTED_LLMS, initialize_llm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('agui-server.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

APP_ROOT = "/Users/parag.kulkarni/ai-workspace/aws-infra-agent-bot"
UI_DIR = f"{APP_ROOT}/ui"

app = FastAPI(title="AWS Infra Agent Bot - AG-UI")
app.mount("/static", StaticFiles(directory=UI_DIR), name="static")

logger.info("=" * 80)
logger.info("AWS Infra Agent Bot - AG-UI Server Starting")
logger.info(f"UI Directory: {UI_DIR}")
logger.info("=" * 80)

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
    logger.debug("Serving index.html")
    return FileResponse(f"{UI_DIR}/index.html")


@app.get("/api/models")
async def list_models():
    logger.info("API Request: GET /api/models - Listing available LLM providers")
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
    logger.info(f"Returning {len(providers)} LLM providers")
    return JSONResponse({"providers": providers})


def get_llm(provider: str, model: Optional[str], credential_source: Optional[str]):
    cache_key = f"{provider}:{model or ''}:{credential_source or 'auto'}"
    if cache_key in llm_cache:
        logger.debug(f"LLM cache hit: {cache_key}")
        return llm_cache[cache_key]

    logger.info(f"Initializing LLM - Provider: {provider}, Model: {model or 'default'}, Credential Source: {credential_source or 'auto'}")
    llm = initialize_llm(provider, model=model, preferred_source=credential_source)
    llm_cache[cache_key] = llm
    logger.info(f"LLM initialized and cached: {cache_key}")
    return llm


def sse_event(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


def now_ms() -> int:
    return int(time.time() * 1000)


@app.post("/api/run")
async def run_agent(payload: RunRequest):
    logger.info("=" * 80)
    logger.info("API Request: POST /api/run - New user query received")
    logger.info(f"Provider: {payload.provider}, Model: {payload.model or 'default'}")
    logger.info(f"Credential Source: {payload.credentialSource or 'auto'}")
    logger.info(f"Thread ID: {payload.threadId}")
    logger.info(f"Message Length: {len(payload.message)} characters")
    
    if not payload.message.strip():
        logger.warning("Request rejected: Empty message")
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    if payload.provider not in SUPPORTED_LLMS:
        logger.error(f"Request rejected: Unsupported provider '{payload.provider}'")
        raise HTTPException(status_code=400, detail="Unsupported provider")

    run_id = str(uuid.uuid4())
    message_id = str(uuid.uuid4())
    thread_id = payload.threadId or str(uuid.uuid4())
    
    logger.info(f"Run ID: {run_id}")
    logger.info(f"Message ID: {message_id}")

    history = conversation_store.setdefault(thread_id, [])
    logger.debug(f"Conversation history size: {len(history)} messages")
    history.append(HumanMessage(content=payload.message))

    def stream():
        try:
            logger.info(f"[{run_id}] Stream started for thread {thread_id}")
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
            
            logger.info(f"[{run_id}] Invoking LLM with conversation history")

            llm = get_llm(payload.provider, payload.model, payload.credentialSource)
            response = llm.invoke(history)
            response_text = response.content if response else ""
            if not response_text.strip():
                logger.warning(f"[{run_id}] LLM returned empty response")
                response_text = "No response generated."
            history.append(AIMessage(content=response_text))
            
            logger.info(f"[{run_id}] LLM response generated - Length: {len(response_text)} characters")
            logger.debug(f"[{run_id}] Updated conversation history size: {len(history)} messages")

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
            
            logger.info(f"[{run_id}] Stream completed successfully")

            yield sse_event({
                "type": "RUN_FINISHED",
                "runId": run_id,
                "threadId": thread_id,
                "timestamp": now_ms(),
            })

        except Exception as exc:
            logger.error(f"[{run_id}] Error during stream execution: {str(exc)}", exc_info=True)
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

    port = int(os.getenv("PORT", "8000"))
    logger.info(f"Starting uvicorn server on http://0.0.0.0:{port}")
    logger.info(f"Reload mode: enabled")
    uvicorn.run("agui_server:app", host="0.0.0.0", port=port, reload=True)
