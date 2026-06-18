"""联网搜索模块：Bing Web Search API"""
import httpx
from loguru import logger
from app.core.config import settings

BING_API_URL = "https://api.bing.microsoft.com/v7.0/search"


async def bing_search(query: str, top_k: int = 5) -> list[dict]:
    if not settings.bing_search_api_key:
        logger.warning("Bing API Key 未配置")
        return []

    try:
        headers = {"Ocp-Apim-Subscription-Key": settings.bing_search_api_key}
        params = {"q": query, "count": top_k, "mkt": "zh-CN"}

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(BING_API_URL, headers=headers, params=params)

            if response.status_code != 200:
                logger.error(f"Bing 搜索失败: {response.status_code}")
                return []

            data = response.json()
            results = data.get("webPages", {}).get("value", [])
            logger.info(f"Bing 搜索: {query} → {len(results)} 条结果")
            return [
                {"title": r.get("name", ""), "url": r.get("url", ""), "snippet": r.get("snippet", "")}
                for r in results[:top_k]
            ]

    except Exception as e:
        logger.error(f"Bing 搜索异常: {e}")
        return []
