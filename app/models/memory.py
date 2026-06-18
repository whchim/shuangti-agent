from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MemoryFact(BaseModel):
    id: str
    user_id: str
    fact: str
    source_session_id: Optional[str] = None
    created_at: str
    updated_at: str


class MemoryFactsResponse(BaseModel):
    facts: list[MemoryFact]
    total: int
