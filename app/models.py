from typing import Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)


class QueryResponse(BaseModel):
    query: str
    generated_logic: str
    result: Any
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    explanation: str
