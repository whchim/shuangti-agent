"""知识库管理 API"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from app.models.knowledge import DocumentUploadResponse, DocumentListResponse, ReloadResponse
from app.service.knowledge_service import upload_and_index, list_documents, delete_document, reload_all_documents

router = APIRouter(prefix="/api/knowledge", tags=["知识库管理"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form(default="未分类"),
):
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")

    content = await file.read()
    try:
        result = await upload_and_index(content, file.filename, category)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def get_documents():
    docs = await list_documents()
    return {"documents": docs, "total": len(docs)}


@router.delete("/documents/{doc_id}")
async def remove_document(doc_id: str):
    deleted = await delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"message": "已删除"}


@router.post("/reload")
async def reload_documents():
    try:
        result = await reload_all_documents()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
