from pydantic import BaseModel, Field
from typing import List, Optional


class ChatRequest(BaseModel):
    message: Optional[str] = Field(None, description="User message")
    query: Optional[str] = Field(None, description="Legacy key support")
    top_k: int = 6
    must_cite: bool = True
    summary: Optional[str] = None

    @property
    def text(self) -> str:
        return self.message or self.query or ""


class Source(BaseModel):
    doc: str
    page: int
    score: float = 0.0
    snippet: str = ""


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source] = []


