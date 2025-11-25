from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
import logging
import os

from db import engine, Base, get_top_items_for_user
from schemas import ChatRequest, ChatResponse, ErrorResponse
from fastapi.responses import JSONResponse
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tracers.context import tracing_v2_enabled

app = FastAPI()

llm = ChatOpenAI(
    model="openai/gpt-4o-mini",
    temperature=0.7,
    timeout=15,
    max_retries=0,
)

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a helpful assistant. Always greet {user_name}. Respond in a {tone} tone.\n"
     "Use the following Context if it is relevant to the user's request. If your final answer relied on the Context, set used_context to True; otherwise set it to False.\n\n"
     "Context:\n{context_text}"),
    ("human", "{message}")
])
structured_llm = llm.with_structured_output(ChatResponse)
chain = prompt | structured_llm

ALLOWED_TONES = {"friendly", "formal", "cheerful", "concise", "sarcastic"}


def get_current_user():
    return {"name": "Yaroslav", "email": "yaroslav@gmail.com"}


@app.post("/chat", response_model=ChatResponse, responses={400: {"model": ErrorResponse}})
def chat(request: ChatRequest):
    user = get_current_user()
    user_name = user.get("name") or user.get("email") or "User"
    user_email = user.get("email") or "user@example.com"

    msg = (request.message or "").strip()
    if not msg:
        return JSONResponse(status_code=400, content={"error": "Message cannot be empty"})

    tone = (request.tone or "friendly").lower()
    if tone not in ALLOWED_TONES:
        return JSONResponse(status_code=400, content={"error": f"Invalid tone. Allowed: {', '.join(sorted(ALLOWED_TONES))}"})

    items = get_top_items_for_user(user_email, limit=3)
    context_text = "\n".join(f"- {t}" for t in items) if items else "None"

    try:
        use_tracing = os.getenv("LANGSMITH_TRACING", "").lower() == "true" and bool(os.getenv("LANGSMITH_API_KEY"))
        if use_tracing:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "")
            os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
            project = os.getenv("LANGSMITH_PROJECT", "project-10")
            with tracing_v2_enabled(project_name=project):
                result = chain.invoke({"user_name": user_name, "tone": tone, "message": msg, "context_text": context_text})
        else:
            result = chain.invoke({"user_name": user_name, "tone": tone, "message": msg, "context_text": context_text})
        return result
    except Exception:
        logging.exception("LLM provider error")
        return JSONResponse(status_code=502, content={"error": "LLM provider error"})