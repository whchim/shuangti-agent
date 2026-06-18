"""知识库初始导入脚本
用法：python scripts/load_knowledge.py --path ./knowledge_base
"""
import asyncio
import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from app.core.database import init_db
from app.service.knowledge_service import upload_and_index
from app.llm.zhipu import ZhipuAdapter


async def main():
    parser = argparse.ArgumentParser(description="导入知识库文档")
    parser.add_argument("--path", required=True, help="知识库目录路径")
    parser.add_argument("--category", default="未分类", help="文档分类标签")
    args = parser.parse_args()

    await init_db()

    if not os.path.isdir(args.path):
        logger.error(f"目录不存在: {args.path}")
        return

    llm = ZhipuAdapter()

    for filename in os.listdir(args.path):
        filepath = os.path.join(args.path, filename)
        if not os.path.isfile(filepath):
            continue
        ext = os.path.splitext(filename)[1].lower()
        if ext not in (".pdf", ".txt", ".md"):
            continue

        logger.info(f"正在导入: {filename}")
        with open(filepath, "rb") as f:
            content = f.read()
        try:
            result = await upload_and_index(content, filename, args.category, llm)
            logger.info(f"导入成功: {filename} -> {result['chunk_count']} chunks")
        except Exception as e:
            logger.error(f"导入失败: {filename}, 错误: {e}")

    logger.info("知识库导入完成！")


if __name__ == "__main__":
    asyncio.run(main())
