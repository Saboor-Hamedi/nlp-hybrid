from typing import Optional
import anyio
from fastapi import APIRouter, Request, Form, Query, Depends
from fastapi.responses import HTMLResponse

from api.dependencies import get_async_db, get_nlp_model, templates
from db.operations.AsyncDocumentManager import AsyncDocumentManager
from utils.analytics.topic_modeling import get_topics, predict_topic
from utils.analytics.bert_topic import get_bert_topics, predict_bert_topic

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
        # Inject carried forensic context from search results (with sanitization)
        lda_label = lda if lda and lda not in ['undefined', 'N/A'] else None
        bert_label = bert if bert and bert not in ['undefined', 'N/A'] else None
        
        # Self-Healing Logic: Total Reconstruction for LDA and BERT
        if not lda_label or not lda_kw or lda_kw == 'undefined' or not bert_label or not bert_kw or bert_kw == 'undefined':
            try:
                # Fetch a global sample for high-fidelity context
                rows = await conn.fetch('SELECT content FROM document ORDER BY random() LIMIT 100')
                training_data = [r['content'] for r in rows]
                
                if training_data:
                    # 1. LDA Reconstruction
                    if not lda_label or not lda_kw or lda_kw == 'undefined':
                        lda_info, lda_model, dictionary = await anyio.to_thread.run_sync(get_topics, training_data, 5)
                        topic_id = await anyio.to_thread.run_sync(predict_topic, result['content'], lda_model, dictionary)
                        lda_label = f"LDA Theme {topic_id + 1}"
                        # Extract 10 keywords with weights: {word: weight}
                        topic_segments = lda_info[topic_id][1].split(' + ')[:10]
                        result['lda_keywords'] = {
                            s.split('*')[1].replace('"', ''): float(s.split('*')[0]) 
                            for s in topic_segments
                        }
                    
                    # 2. BERT Reconstruction
                    if not bert_label or not bert_kw or bert_kw == 'undefined':
                        bert_info, bert_kmeans = await anyio.to_thread.run_sync(get_bert_topics, training_data, model, 5)
                        bert_id = await anyio.to_thread.run_sync(predict_bert_topic, result['content'], model, bert_kmeans)
                        bert_label = f"BERT Theme {bert_id + 1}"
                        # BERT keywords (extended to 10)
                        result['bert_keywords'] = [k.strip() for k in bert_info[bert_id][1].split(',')[:10]]
            except Exception as e:
                print(f"Parallel Healing Error: {e}")

        result['lda_topic_label'] = lda_label or "LDA Analysis: Pending"
        result['bert_topic_label'] = bert_label or "BERT Context: Pending"
        
        # Final Signal Matrix Assembly (Supporting both weighted dicts and plain lists)
        if not result.get('lda_keywords'):
            if lda_kw and lda_kw != 'undefined':
                result['lda_keywords'] = {}
                for part in lda_kw.split(','):
                    if ':' in part:
                        k, v = part.split(':')
                        result['lda_keywords'][k.strip()] = float(v)
                    else:
                        result['lda_keywords'][part.strip()] = 1.0 # Default weight
            else:
                result['lda_keywords'] = {}
        
        if not result.get('bert_keywords'):
            result['bert_keywords'] = [k.strip() for k in bert_kw.split(',') if k.strip()] if bert_kw and bert_kw != 'undefined' else []

    return templates.TemplateResponse("static/show.html", {
        "request": request, 
        "result": result
    })
