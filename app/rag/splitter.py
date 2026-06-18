"""文档分割策略"""
from langchain.text_splitter import RecursiveCharacterTextSplitter


def get_splitter(chunk_size: int = 500, chunk_overlap: int = 50) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "；", "，", " ", ""],
        keep_separator=True,
    )


def split_document(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    splitter = get_splitter(chunk_size, chunk_overlap)
    chunks = splitter.split_text(text)
    return [c for c in chunks if c.strip()]
