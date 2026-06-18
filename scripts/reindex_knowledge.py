"""知识库重建索引脚本
用法：python scripts/reindex_knowledge.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from app.core.database import init_db, close_db
from app.service.knowledge_service import reload_all_documents
from app.llm.zhipu import ZhipuAdapter


async def main():
    logger.info("开始重建知识库索引...")
    await init_db()

    llm = ZhipuAdapter()
    result = await reload_all_documents(llm)

    logger.info(f"重建完成: {result}")
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
