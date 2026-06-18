"""联网搜索模块：Tavily Search API"""
import httpx
from loguru import logger
from app.core.config import settings

TAVILY_API_URL = "https://api.tavily.com/search"


async def tavily_search(query: str, top_k: int = 5) -> list[dict]:
    if not settings.tavily_api_key:
        logger.warning("Tavily API Key 未配置")
        return []

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                TAVILY_API_URL,
                json={
                    "api_key": settings.tavily_api_key,
                    "query": query,
                    "max_results": top_k,
                    "search_depth": "basic",
                },
            )

            if response.status_code != 200:
                logger.error(f"Tavily 搜索失败: {response.status_code}")
                return []

            data = response.json()
            results = data.get("results", [])
            logger.info(f"Tavily 搜索: {query} → {len(results)} 条结果")
            return [
                {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")}
                for r in results[:top_k]
            ]

    except Exception as e:
        logger.error(f"Tavily 搜索异常: {e}")
        return []
