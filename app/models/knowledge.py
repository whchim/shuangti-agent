from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    category: str
    status: str
    chunk_count: int = 0
    created_at: str


class DocumentItem(BaseModel):
    id: str
    filename: str
    category: str
    chunk_count: int
    status: str
    created_at: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentItem]
    total: int


class ReloadResponse(BaseModel):
    message: str
    status: str
    total_documents: int


class UrlIngestRequest(BaseModel):
    url: str
    category: str = "未分类"


class UrlIngestResponse(BaseModel):
    id: str
    url: str
    title: str
    category: str
    chunk_count: int
