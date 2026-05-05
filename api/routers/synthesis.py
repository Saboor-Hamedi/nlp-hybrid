from fastapi import APIRouter, Request, Depends, HTTPException
from api.dependencies import get_async_db
from utils.llm.deepseek_client import DeepSeekClient
import httpx
from typing import List, Dict, Any

router = APIRouter()
llm = DeepSeekClient()

@router.post("/api/synthesis")
async def forensic_synthesis(request: Request, conn = Depends(get_async_db)):
    """
    RAG Orchestrator: Combines retrieval and generation to provide 
    synthesized forensic answers.
    """
    data = await request.json()
    query = data.get("query")
    context_docs = data.get("context_docs", [])

    if not query:
        raise HTTPException(status_code=400, detail="Search query is required for synthesis")
    
    synthesis = await llm.synthesize(query, context_docs)
    return {"synthesis": synthesis}

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
