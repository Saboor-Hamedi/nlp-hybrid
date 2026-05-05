from fastapi import APIRouter, Depends, HTTPException, status, Request
from api.dependencies import get_async_db, get_nlp_model
from db.operations.AsyncDocumentManager import AsyncDocumentManager

router = APIRouter(tags=["CRUD"])

@router.delete("/api/docs/{doc_id}")
async def delete_document(
    doc_id: int,
    conn = Depends(get_async_db),
    model = Depends(get_nlp_model)
):
    """Surgically remove a document."""
    await conn.execute("DELETE FROM document WHERE id = $1", doc_id)
    return {"status": "success"}

@router.post("/api/docs")
async def create_document(
    request: Request,
    conn = Depends(get_async_db),
    model = Depends(get_nlp_model)
):
    """Inject a new document into the archive."""
    data = await request.json()
    content = data.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")
    
    doc_id = await conn.fetchval(
        "INSERT INTO document (content, language) VALUES ($1, 'en') RETURNING id", 
        content
    )
    return {"status": "success", "id": doc_id}

@router.put("/api/docs/{doc_id}")
async def update_document(
    doc_id: int,
    request: Request,
    conn = Depends(get_async_db),
    model = Depends(get_nlp_model)
):
    """Update existing document content."""
    data = await request.json()
    content = data.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")
    
    await conn.execute("UPDATE document SET content = $1 WHERE id = $2", content, doc_id)
    return {"status": "success"}
