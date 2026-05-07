from fastapi import APIRouter, Depends, HTTPException, status, Request
from api.dependencies import get_async_db, get_nlp_model
from db.operations.AsyncDocumentManager import AsyncDocumentManager

router = APIRouter(tags=["CRUD"])

@router.delete("/api/docs/{doc_id}")
async def delete_document(
    doc_id: int,
    conn = Depends(get_async_db)
):
    """Surgically remove a document from all forensic brains."""
    from hybrid.LlamaIndexMind import LlamaIndexMind
    
    # 1. Archive Purge
    await conn.execute("DELETE FROM document WHERE id = $1", doc_id)
    
    # 2. Legacy Search Purge
    await conn.execute("DELETE FROM document_embedding WHERE doc_id = $1", doc_id)
    
    # 3. Modern Chat Purge (Deep-Purge Strategy)
    await conn.execute("""
        DELETE FROM forensic_index 
        WHERE (metadata_ ->> 'doc_id')::text = $1
    """, str(doc_id))
    
    # 4. Brain Reset
    LlamaIndexMind._instance = None
    
    return {"status": "success"}

@router.post("/api/docs")
async def create_document(
    request: Request,
    conn = Depends(get_async_db)
):
    """Inject a new document into the archive and neural index."""
    from hybrid.LlamaIndexMind import LlamaIndexMind
    from llama_index.core import Document
    
    data = await request.json()
    content = data.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")
    
    # 1. Archive Entry
    doc_id = await conn.fetchval(
        "INSERT INTO document (content, language) VALUES ($1, 'en') RETURNING id", 
        content
    )
    
    # 2. Neural Ingestion
    try:
        mind = LlamaIndexMind()
        new_doc = Document(text=content, metadata={"doc_id": doc_id})
        mind.index.insert(new_doc)
    except Exception as e:
        print(f"🔥 NEURAL INGESTION ERROR: {e}")
        
    return {"status": "success", "id": doc_id}

@router.put("/api/docs/{doc_id}")
async def update_document(
    doc_id: int,
    request: Request,
    conn = Depends(get_async_db)
):
    """Update document and refresh its neural embedding."""
    from hybrid.LlamaIndexMind import LlamaIndexMind
    from llama_index.core import Document
    
    data = await request.json()
    content = data.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")
    
    # 1. Update Primary Archive
    await conn.execute("UPDATE document SET content = $1 WHERE id = $2", content, doc_id)
    
    # 2. Neural Re-Indexing (Surgical Wipe Strategy)
    try:
        from hybrid.LlamaIndexMind import LlamaIndexMind
        from llama_index.core import Document
        from api.dependencies import get_nlp_model
        
        # 1. Hard Purge Legacy Brain
        await conn.execute("DELETE FROM document_embedding WHERE doc_id = $1", doc_id)
        
        # 2. Clean Re-Insert Legacy Brain
        model = get_nlp_model()
        new_vec = model.encode(content).tolist()
        await conn.execute("INSERT INTO document_embedding (doc_id, embedding) VALUES ($1, $2)", doc_id, new_vec)
        
        # 3. Hard Purge Modern Brain
        await conn.execute("DELETE FROM forensic_index WHERE (metadata_ ->> 'doc_id')::text = $1", str(doc_id))
        
        # 4. Clean Re-Insert Modern Brain
        mind = LlamaIndexMind()
        new_doc = Document(text=content, metadata={"doc_id": doc_id})
        mind.index.insert(new_doc)
        
        # 5. Global Brain Reset
        LlamaIndexMind._instance = None
        print(f"✅ [Neural Forge] Hard Purge Complete for Record #{doc_id}")
    except Exception as e:
        print(f"🔥 SURGICAL WIPE FAILURE: {e}")
        
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
