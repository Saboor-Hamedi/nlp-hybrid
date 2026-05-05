from typing import Optional
import anyio
from fastapi import APIRouter, Request, Form, Query, Depends
from fastapi.responses import HTMLResponse

from api.dependencies import get_async_db, get_nlp_model, templates
from db.operations.AsyncDocumentManager import AsyncDocumentManager
from utils.analytics.topic_modeling import get_topics, predict_topic

router = APIRouter(tags=["Archive"])

@router.get("/", response_class=HTMLResponse)
@router.post("/", response_class=HTMLResponse)
async def home(
    request: Request, 
    query: Optional[str] = Form(None), 
    get_query: Optional[str] = Query(None, alias="query"),
    conn = Depends(get_async_db),
    model = Depends(get_nlp_model)
):
    """
    Main dashboard entry point. Displays recent documents and corpus statistics.
    """
    search_query = (query or get_query or "").strip()
    
    manager = AsyncDocumentManager(conn, model)
    results = await manager.select(limit=10)
    total_count = await manager.get_total_count()

    # Process documents for thematic tagging (LDA)
    if results:
        # Fetch high-quality training sample for on-the-fly LDA
        rows = await conn.fetch('SELECT content FROM document ORDER BY random() LIMIT 10')
        training_data = [r['content'] for r in rows]
        
        if training_data:
            try:
                # Offload blocking ML training to a separate threadpool
                _, lda_model, dictionary = await anyio.to_thread.run_sync(
                    get_topics, training_data, min(10, len(training_data))
                )
                
                # Batch prediction
                for doc in results:
                    doc['relevance_score'] = 'N/A'
                    topic_id = await anyio.to_thread.run_sync(
                        predict_topic, doc['content'], lda_model, dictionary
                    )
                    doc['tag'] = f'LDA Topic {topic_id + 1}'
            except Exception as e:
                print(f"Operational Warning: LDA inference bypassed - {e}")
    else:
        results = []

    return templates.TemplateResponse("static/content.html", {
        "request": request, 
        "results": results, 
        "query": search_query,
        "total_count": total_count
    })

@router.get("/show/{doc_id}", response_class=HTMLResponse)
async def show(
    request: Request, 
    doc_id: int, 
    lda: Optional[str] = Query(None),
    bert: Optional[str] = Query(None),
    lda_kw: Optional[str] = Query(None),
    bert_kw: Optional[str] = Query(None),
    conn = Depends(get_async_db), 
    model = Depends(get_nlp_model)
):
    """
    Retreive and display a full forensic document analysis.
    """
    manager = AsyncDocumentManager(conn, model)
    result = await manager.show(doc_id)
    
    if result:
        # Inject carried forensic context from search results
        result['lda_topic_label'] = lda
        result['bert_topic_label'] = bert
        
        # Parse signal matrices
        result['lda_keywords'] = [k.strip() for k in lda_kw.split(',')] if lda_kw else []
        result['bert_keywords'] = [k.strip() for k in bert_kw.split(',')] if bert_kw else []

    return templates.TemplateResponse("static/show.html", {
        "request": request, 
        "result": result
    })
