from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class SearchMode(str, Enum):
    knowledge_base = "knowledge_base"
    web_search = "web_search"
    hybrid = "hybrid"


class ChatSendRequest(BaseModel):
    session_id: Optional[str] = None  # 新会话时不传
    message: str = Field(min_length=1, max_length=2000)
    model: str = "zhipu"
    knowledge_base_ids: list[str] = []
    search_mode: SearchMode = SearchMode.knowledge_base


class Source(BaseModel):
    doc_name: str
    chunk: str
    page: Optional[int] = None


class WebSource(BaseModel):
    title: str
    url: str
    snippet: str


class ChatSendResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[Source] = []
    web_sources: list[WebSource] = []
    created_at: datetime


class MessageItem(BaseModel):
    id: str
    role: str
    content: str
    round_number: int
    created_at: str


class SessionItem(BaseModel):
    id: str
    title: str
    session_type: str
    created_at: str
    updated_at: str


class SessionDetail(BaseModel):
    id: str
    title: str
    session_type: str
    messages: list[MessageItem]
    total: int
    page: int
    page_size: int
