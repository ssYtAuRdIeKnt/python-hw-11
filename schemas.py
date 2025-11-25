from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    tone: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    used_context: bool


class ErrorResponse(BaseModel):
    error: str