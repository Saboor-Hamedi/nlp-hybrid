from typing import Optional, List, Dict, Any
import anyio
from fastapi import APIRouter, Request, Form, Query, Depends
from fastapi.responses import HTMLResponse

from api.dependencies import get_async_db, get_nlp_model, templates
from api.helpers import parse_lda_keywords, parse_bert_keywords
from hybrid.async_hybrid_search import search_hybrid_async
from utils.analytics.topic_modeling import get_topics, predict_topic
from utils.analytics.bert_topic import get_bert_topics, predict_bert_topic

from api.schemas import SearchQuery

router = APIRouter(tags=["Search"])

@router.get("/api/quick-search")
async def quick_search(
    query: str = Query(..., min_length=2),
    conn = Depends(get_async_db),
    model = Depends(get_nlp_model)
):
    """Instant search endpoint for the command palette with auto-validation."""
    # We use the same robust hybrid engine but limit to top 5 for speed
    results, _ = await search_hybrid_async(query, conn, model, top_k=5)
    
    formatted = [
        {"id": r[0], "content": r[1][:80] + "...", "score": f"{r[2]:.2f}"}
        for r in results
    ]
    return formatted

@router.get("/search", response_class=HTMLResponse)
@router.post("/search", response_class=HTMLResponse)
async def search(
    request: Request, 
    query: Optional[str] = Form(None), 
    get_query: Optional[str] = Query(None, alias="query"),
    conn = Depends(get_async_db),
    model = Depends(get_nlp_model)
):
    """
    Perform hybrid forensic search with strict Pydantic input validation.
    """
    q_str = (query or get_query or "").strip()
    
    # Manual trigger of Pydantic validation for mixed source inputs
    try:
        validated = SearchQuery(query=q_str)
        q = validated.query
    except Exception as e:
        return templates.TemplateResponse("static/search.html", {
            "request": request, 
            "results": [], 
            "query": q_str, 
            "error": f"Validation Error: {str(e)}"
        })
        
    # Execute Async Hybrid Search
    results, stats = await search_hybrid_async(q, conn, model)
    
    # Contextual Topic Discovery on search results
    training_data = [r[1] for r in results]
    dynamic_k = max(1, min(5, len(training_data)))

    lda_topics, lda_model, dictionary = [], None, None
    bert_topics, bert_kmeans = [], None

    if training_data:
        try: 
            lda_topics, lda_model, dictionary = await anyio.to_thread.run_sync(
                get_topics, training_data, dynamic_k
            )
        except Exception as e: print(f"LDA Discovery Error: {e}")
            
        try: 
            bert_topics, bert_kmeans = await anyio.to_thread.run_sync(
                get_bert_topics, training_data, model, dynamic_k
            )
        except Exception as e: print(f"BERT Discovery Error: {e}")

    # Build final response payload
    results_dict: List[Dict[str, Any]] = []
    for r in results:
        lda_topic_id, bert_topic_id = 0, 0
        if lda_model and dictionary:
            try: lda_topic_id = await anyio.to_thread.run_sync(predict_topic, r[1], lda_model, dictionary)
            except: pass
        if bert_kmeans:
            try: bert_topic_id = await anyio.to_thread.run_sync(predict_bert_topic, r[1], model, bert_kmeans)
            except: pass

        lda_keywords, bert_keywords = {}, {}
        
        # Keyword extraction for UI badges
        if lda_topics and lda_topic_id < len(lda_topics):
            try:
                topic_content = lda_topics[lda_topic_id]
                if isinstance(topic_content, (tuple, list)) and len(topic_content) > 1:
                    lda_keywords = parse_lda_keywords(topic_content[1])
            except: pass

        if bert_topics and bert_topic_id < len(bert_topics):
            try:
                bert_content = bert_topics[bert_topic_id]
                if isinstance(bert_content, (tuple, list)) and len(bert_content) > 1:
                    bert_keywords = parse_bert_keywords(bert_content)
            except: pass

        results_dict.append({
            "id": r[0], 
            "content": r[1], 
            "relevance_score": r[2], 
            "language": r[3], 
            "created_at": r[4],
            "lda_topic_id": lda_topic_id, 
            "lda_topic_label": f"LDA Theme {lda_topic_id + 1}" if lda_topics else "N/A",
            "bert_topic_id": bert_topic_id, 
            "bert_topic_label": f"BERT Theme {bert_topic_id + 1}" if bert_topics else "N/A",
            "lda_keywords": lda_keywords, 
            "bert_keywords": bert_keywords
        })

    return templates.TemplateResponse("static/search.html", {
        "request": request, 
        "results": results_dict, 
        "query": q,
        "lda_topics": lda_topics, 
        "bert_topics": bert_topics
    })
