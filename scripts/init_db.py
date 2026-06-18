"""数据库初始化脚本"""
import asyncio
import sys
import os

# 将项目根目录加入 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, close_db
from loguru import logger


async def main():
    logger.info("开始初始化数据库...")
    await init_db()
    logger.info("数据库初始化完成！")


if __name__ == "__main__":
    asyncio.run(main())
