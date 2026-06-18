"""文档加载器：支持 PDF、TXT、Markdown"""
import os
from pathlib import Path
from loguru import logger


async def load_document(file_path: str) -> str:
    """根据文件扩展名自动选择加载器"""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return await load_pdf(file_path)
    elif ext in (".txt", ".md"):
        return await load_text(file_path)
    else:
        raise ValueError(f"不支持的文件格式: {ext}")


async def load_pdf(file_path: str) -> str:
    try:
        from pypdf2 import PdfReader
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        logger.info(f"PDF 加载完成: {file_path}, 共 {len(reader.pages)} 页")
        return text.strip()
    except ImportError:
        raise ImportError("请安装 pypdf2 以支持 PDF 解析")


async def load_text(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    logger.info(f"文本加载完成: {file_path}, 共 {len(text)} 字符")
    return text.strip()
