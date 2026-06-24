"""联网搜索 API"""
from fastapi import APIRouter, HTTPException
from app.models.search import SearchQueryRequest, SearchQueryResponse, SearchConfig, SearchConfigUpdate
from app.service.search_service import do_search, get_search_config

router = APIRouter(prefix="/api/search", tags=["联网搜索"])


@router.post("/query", response_model=SearchQueryResponse)
async def search_query(req: SearchQueryRequest):
    results = await do_search(req.query, req.engine, req.top_k)
    return {"query": req.query, "results": results, "engine": req.engine}


@router.get("/config", response_model=SearchConfig)
async def get_config():
    return get_search_config()


@router.put("/config", response_model=SearchConfig)
async def update_config(req: SearchConfigUpdate):
    from app.core.config import settings
    if req.default_search_engine:
        settings.default_search_engine = req.default_search_engine
    if req.tavily_api_key is not None:
        settings.tavily_api_key = req.tavily_api_key
    if req.bing_search_api_key is not None:
        settings.bing_search_api_key = req.bing_search_api_key
    return get_search_config()
