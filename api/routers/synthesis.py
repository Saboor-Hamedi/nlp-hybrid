from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import StreamingResponse
from api.dependencies import get_async_db
from hybrid.RAGMind import RAGMind

router = APIRouter(tags=["Synthesis"])

@router.post("/api/synthesis")
async def forensic_synthesis(request: Request, conn = Depends(get_async_db)):
    """
    RAG Orchestrator: Provides streaming synthesized forensic answers via RAGMind.
    """
    data = await request.json()
    query = data.get("query")
    context_docs = data.get("context_docs", [])
    mode = data.get("mode", "local")

    if not query:
        raise HTTPException(status_code=400, detail="Search query is required")
    
    mind = RAGMind(conn)
    return StreamingResponse(
        await mind.synthesize_stream(query, context_docs, mode), 
        media_type="text/plain"
    )

@router.post("/api/synthesis/save")
async def save_forensic_insight(request: Request, conn = Depends(get_async_db)):
    """
    Neural Indexer: Commits a synthesized briefing via RAGMind's archival pipeline.
    """
    data = await request.json()
    query = data.get("query")
    content = data.get("content")
    mode = data.get("mode", "local")

    if not query or not content:
        raise HTTPException(status_code=400, detail="Incomplete data for registry entry.")

    try:
        mind = RAGMind(conn)
        doc_id = await mind.archive_insight(query, content, mode)
        return {
            "status": "success", 
            "message": "Insight archived and vectorized successfully.", 
            "doc_id": doc_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/refine")
async def refine_document(request: Request, conn = Depends(get_async_db)):
    """
    Surgical Refiner: Uses RAGMind to clean and normalize forensic text.
    """
    data = await request.json()
    text = data.get("text", "")
    custom_instruction = data.get("prompt", "")
    
    try:
        mind = RAGMind(conn)
        refined_text = await mind.refine(text, custom_instruction)
        return {"refined_text": refined_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
