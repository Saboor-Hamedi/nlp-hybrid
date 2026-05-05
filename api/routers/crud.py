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
@router.get("/api/docs/{doc_id}")
async def get_document(doc_id: int, conn = Depends(get_async_db)):
    """Retrieve full document forensics for the viewer."""
    try:
        # Fetch base document data
        row = await conn.fetchrow("""
            SELECT id, content, language, created_at 
            FROM document WHERE id = $1
        """, doc_id)
        
        if not row:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Initialize results
        res = {
            "id": row['id'],
            "content": row['content'],
            "language": row['language'],
            "created_at": row['created_at'].strftime("%Y-%m-%d %H:%M:%S") if row['created_at'] else "N/A",
            "lda_tag": "Analysis Pending",
            "lda_keywords": {},
            "bert_tag": "Vector Pending",
            "bert_keywords": []
        }

        # Try to fetch thematic data if columns exist (Optional/Future proof)
        try:
            thematic = await conn.fetchrow("SELECT lda_topic_label, lda_keywords, bert_topic_label, bert_keywords FROM document WHERE id = $1", doc_id)
            if thematic:
                import json
                res["lda_tag"] = thematic['lda_topic_label'] or "N/A"
                res["bert_tag"] = thematic['bert_topic_label'] or "N/A"
                if thematic['lda_keywords']:
                    res["lda_keywords"] = json.loads(thematic['lda_keywords']) if isinstance(thematic['lda_keywords'], str) else thematic['lda_keywords']
                if thematic['bert_keywords']:
                    res["bert_keywords"] = json.loads(thematic['bert_keywords']) if isinstance(thematic['bert_keywords'], str) else thematic['bert_keywords']
        except:
            pass # Columns don't exist yet, that's fine

        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
