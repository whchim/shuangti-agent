from typing import Optional
from pydantic import BaseModel


class SearchQueryRequest(BaseModel):
    query: str
    engine: str = "tavily"
    top_k: int = 5


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str


class SearchQueryResponse(BaseModel):
    query: str
    results: list[SearchResult]
    engine: str


class SearchConfig(BaseModel):
    default_engine: str
    engines: list[str]
    tavily_available: bool


class SearchConfigUpdate(BaseModel):
    default_search_engine: Optional[str] = None
    tavily_api_key: Optional[str] = None
