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
    # 运行时切换搜索引擎（通过全局配置）
    from app.core.config import settings
    settings.default_search_engine = req.default_engine
    return get_search_config()
