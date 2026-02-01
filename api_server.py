from fastapi import FastAPI, HTTPException, Request
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Optional
import os
import logging
import sys
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from llm_config import initialize_llm
from terraform_tools import get_terraform_tools
from langchain_classic.agents import initialize_agent, AgentType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('.api-server.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str
    provider: Optional[str] = "perplexity"
    history: Optional[List[dict]] = []

class ChatResponse(BaseModel):
    response: str
    history: List[dict]

def dict_to_message(m: dict) -> BaseMessage:
    if m["role"] == "user":
        return HumanMessage(content=m["content"])
    return AIMessage(content=m["content"])

def message_to_dict(m: BaseMessage) -> dict:
    if isinstance(m, HumanMessage):
        return {"role": "user", "content": m.content}
    return {"role": "assistant", "content": m.content}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("API Server starting up...")
    yield
    logger.info("API Server shutting down...")

app = FastAPI(title="LangChain Terraform Agent API", lifespan=lifespan)

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    logger.info(f"Received chat request: {request.message[:50]}...")
    try:
        provider = request.provider or os.getenv("LLM_PROVIDER", "perplexity")
        logger.info(f"Using LLM provider: {provider}")

        llm = initialize_llm(provider, temperature=0)

        tools = get_terraform_tools()
        logger.info("Terraform tools loaded")

        # Initialize agent with tools
        agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True
        )
        logger.info("Agent initialized")

        history = [dict_to_message(m) for m in request.history]

        logger.info("Running agent...")
        response = agent.run(input=request.message, chat_history=history)
        logger.info("Agent run complete")

        new_history = request.history + [
            {"role": "user", "content": request.message},
            {"role": "assistant", "content": response}
        ]

        return ChatResponse(response=response, history=new_history)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
