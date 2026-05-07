from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import StreamingResponse
from api.dependencies import get_async_db
from hybrid.LlamaIndexMind import LlamaIndexMind

router = APIRouter(tags=["Synthesis"])

@router.post("/api/synthesis")
async def forensic_synthesis(request: Request, conn = Depends(get_async_db)):
    """
    IndexOllam Orchestrator: Provides streaming conversational research briefings.
    """
    data = await request.json()
    query = data.get("query")
    context_docs = data.get("context_docs", [])

    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    # Initialize the high-density LlamaIndex orchestrator
    mind = LlamaIndexMind()
    
    return StreamingResponse(
        mind.synthesize_stream(query, context_docs), 
        media_type="text/plain"
    )

@router.post("/api/synthesis/save")
async def save_forensic_insight(request: Request, conn = Depends(get_async_db)):
    """
    Neural Indexer: Commits a synthesized briefing to the permanent forensic registry.
    """
    data = await request.json()
    query = data.get("query")
    content = data.get("content")
    
    if not query or not content:
        raise HTTPException(status_code=400, detail="Incomplete data for registry entry.")

    try:
        from llama_index.core import Document
        mind = LlamaIndexMind()
        
        # 1. Database Entry
        query_insert = "INSERT INTO forensic_index (content, created_at) VALUES ($1, NOW()) RETURNING id"
        doc_id = await conn.fetchval(query_insert, f"RESEARCH QUERY: {query}\n\nSYNTHESIS: {content}")
        
        # 2. Neural Vectorization
        doc = Document(text=content, metadata={"doc_id": doc_id, "query": query})
        mind.index.insert(doc)
        
        return {
            "status": "success", 
            "message": "Insight archived and vectorized successfully.", 
            "doc_id": doc_id
        }
    except Exception as e:
        print(f"🔥 ARCHIVE ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/refine")
async def refine_document(request: Request):
    """
    Surgical Refiner: Direct-Injection High-Speed Text Normalization.
    """
    import os, httpx, json
    data = await request.json()
    text = data.get("text", "")
    instruction = data.get("prompt", "Improve grammar and professional tone.")
    api_key = os.getenv("DEEPSEEK_API_KEY")

    if not text or not api_key:
        return {"refined_text": text}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"},
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "You are a professional forensic editor. Return ONLY the refined text."},
                        {"role": "user", "content": f"INSTRUCTION: {instruction}\n\nTEXT:\n{text}"}
                    ],
                    "temperature": 0.3
                }
            )
            
            if resp.status_code == 200:
                result = resp.json()
                refined = result["choices"][0]["message"]["content"]
                return {"refined_text": refined.strip()}
            else:
                print(f"⚠️ REFINE API ERROR {resp.status_code}: {resp.text}")
                return {"refined_text": text} # Fallback to original
    except Exception as e:
        print(f"🔥 REFINE CRITICAL FAILURE: {e}")
        return {"refined_text": text} # Fallback to original
