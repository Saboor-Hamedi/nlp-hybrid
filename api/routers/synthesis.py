from fastapi import APIRouter, Request, Depends, HTTPException
from api.dependencies import get_async_db
from utils.llm.deepseek_client import DeepSeekClient
import httpx
from typing import List, Dict, Any

router = APIRouter()
llm = DeepSeekClient()

from fastapi.responses import StreamingResponse

@router.post("/api/synthesis")
async def forensic_synthesis(request: Request, conn = Depends(get_async_db)):
    """
    RAG Orchestrator: Provides streaming synthesized forensic answers.
    """
    data = await request.json()
    query = data.get("query")
    context_docs = data.get("context_docs", [])
    mode = data.get("mode", "local")

    if not query:
        raise HTTPException(status_code=400, detail="Search query is required")
    
    return StreamingResponse(llm.synthesize_stream(query, context_docs, mode), media_type="text/plain")

from db.db_connection import get_model

@router.post("/api/synthesis/save")
async def save_forensic_insight(request: Request, conn = Depends(get_async_db)):
    """
    Neural Indexer: Commits a synthesized briefing to both the registry and the searchable vector archive.
    """
    data = await request.json()
    query = data.get("query")
    content = data.get("content")
    mode = data.get("mode", "local")

    if not query or not content:
        raise HTTPException(status_code=400, detail="Incomplete data for registry entry.")

    try:
        # 1. Commit to dedicated Forensic Registry
        print(f"📡 Committing insight to registry: {query[:30]}...")
        await conn.execute(
            "INSERT INTO forensic_insights (query, content, mode) VALUES ($1, $2, $3)",
            query, content, mode
        )

        # 2. Integrate into the Main Searchable Archive
        doc_id = await conn.fetchval(
            "INSERT INTO document (content, language) VALUES ($1, 'insight') RETURNING id",
            content
        )

        # 3. Generate and Commit Neural Embedding
        print(f"🧠 Vectorizing insight (ID: {doc_id})...")
        model = get_model()
        if not model:
            raise Exception("Neural Model not initialized")
            
        embedding_list = model.encode(content).tolist()
        # Convert list to pgvector string format: [0.1, 0.2, ...]
        embedding_str = "[" + ",".join(map(str, embedding_list)) + "]"
        
        # Explicitly cast to vector type for asyncpg compliance
        await conn.execute(
            "INSERT INTO document_embedding (doc_id, embedding) VALUES ($1, $2::vector)",
            doc_id, embedding_str
        )

        print(f"✅ Insight (ID: {doc_id}) successfully archived and vectorized.")
        return {"status": "success", "message": "Insight archived and vectorized successfully.", "doc_id": doc_id}
    except Exception as e:
        print(f"🔥 ARCHIVE FAILURE: {str(e)}")
        # Provide more specific detail if possible
        error_detail = f"Database or Neural failure: {str(e)}"
        raise HTTPException(status_code=500, detail=error_detail)

@router.post("/api/refine")
async def refine_document(request: Request):
    """
    Surgical Refiner: Uses AI to clean and normalize forensic text 
    (lowercase, no symbols) for optimal analysis.
    """
    data = await request.json()
    text = data.get("text", "")
    custom_instruction = data.get("prompt", "")
    
    # Default instruction if none provided
    if not custom_instruction:
        custom_instruction = "Clean the text: force lowercase and remove all symbols."

    system_prompt = (
        "You are a Forensic Research Assistant. Your task is to transform the provided text "
        f"based on this specific instruction: '{custom_instruction}'. "
        "Return ONLY the transformed text with no conversational filler or explanations."
    )
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{llm.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {llm.api_key}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text}
                    ],
                    "temperature": 0.1
                }
            )
            data = response.json()
            return {"refined_text": data["choices"][0]["message"]["content"].strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
