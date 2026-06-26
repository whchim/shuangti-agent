"""联网搜索服务"""
from app.core.config import settings
from app.search.tavily_search import tavily_search


async def do_search(query: str, engine: str = None, top_k: int = 5) -> list[dict]:
    engine = engine or settings.default_search_engine
    return await tavily_search(query, top_k)


def get_search_config() -> dict:
    return {
        "default_engine": settings.default_search_engine,
        "engines": ["tavily"],
        "tavily_available": bool(settings.tavily_api_key),
    }
