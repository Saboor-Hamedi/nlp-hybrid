from typing import Optional, List, Dict, Any
import anyio
from fastapi import APIRouter, Request, Form, Query, Depends
from fastapi.responses import HTMLResponse

from api.dependencies import get_async_db, get_nlp_model, templates
from api.helpers import parse_lda_keywords, parse_bert_keywords
from hybrid.RAGHeart import RAGHeart
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
    """Instant search endpoint for the command palette with thematic context."""
    heart = RAGHeart(conn, model)
    results, _ = await heart.search(query, top_k=5)
    
    # Fast-track Topic Analysis for the top 5
    training_data = [r[1] for r in results]
    formatted = []
    
    if training_data:
        try:
            # Perform ultra-fast thematic discovery on the limited sample
            lda_topics, lda_model, dictionary = await anyio.to_thread.run_sync(
                get_topics, training_data, min(3, len(training_data))
            )
            
            # Fast BERT cluster for the palette
            from utils.analytics.topic_modeling import get_bert_topics, predict_bert_topic
            bert_topics, bert_kmeans = await anyio.to_thread.run_sync(
                get_bert_topics, training_data, model, min(3, len(training_data))
            )
            
            for r in results:
                # Predict Topics and extract Signal Matrices
                topic_id = await anyio.to_thread.run_sync(predict_topic, r[1], lda_model, dictionary)
                bert_id = await anyio.to_thread.run_sync(predict_bert_topic, r[1], model, bert_kmeans)
                
                # LDA Keywords
                kw_str = ""
                try:
                    topic_info = lda_topics[topic_id][1]
                    kw_str = ", ".join([w.split('*')[1].replace('"', '') for w in topic_info.split(' + ')[:5]])
                except: pass

                # BERT Keywords
                b_kw_str = ""
                try:
                    b_kw_str = bert_topics[bert_id][1] # BERT keywords are already joined strings
                except: pass

                formatted.append({
                    "id": r[0], 
                    "content": r[1][:80] + "...", 
                    "score": f"{r[2]:.2f}",
                    "lda_topic": f"LDA Theme {topic_id + 1}",
                    "lda_keywords": kw_str,
                    "bert_topic": f"BERT Theme {bert_id + 1}",
                    "bert_keywords": b_kw_str
                })
        except Exception as e:
            # Fallback if analysis fails (speed priority)
            print(f"Quick-Search Analysis Timeout: {e}")
            for r in results:
                formatted.append({
                    "id": r[0], 
                    "content": r[1][:80] + "...", 
                    "score": f"{r[2]:.2f}", 
                    "lda_topic": "N/A",
                    "lda_keywords": "",
                    "bert_topic": "N/A",
                    "bert_keywords": ""
                })
    
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
        return templates.TemplateResponse("pages/search.html", {
            "request": request, 
            "results": [], 
            "query": q_str, 
            "error": f"Validation Error: {str(e)}"
        })
        
    # Execute Async Hybrid Search via RAGHeart
    heart = RAGHeart(conn, model)
    results, stats = await heart.search(q)
    
    # Contextual Topic Discovery on search results
    training_data = [r[1] for r in results]
    # Scaled for forensic breadth (allowing up to 7 themes for dense results)
    dynamic_k = max(1, min(7, len(training_data)))

    lda_topics, lda_model, dictionary = [], None, None
    bert_topics, bert_kmeans = [], None
    lda_coherence = {}

    if training_data:
        try: 
            # Train LDA
            lda_topics, lda_model, dictionary = await anyio.to_thread.run_sync(
                get_topics, training_data, dynamic_k
            )
            
            # Calculate Coherence Scores for the discovered themes
            # We use u_mass for speed in the search loop
            from gensim.models import CoherenceModel
            texts = [preprocess(doc) for doc in training_data]
            corpus = [dictionary.doc2bow(text) for text in texts]
            
            cm = CoherenceModel(model=lda_model, corpus=corpus, dictionary=dictionary, coherence='u_mass')
            # get_coherence_per_topic() returns a list of scores for each topic
            coherence_per_topic = cm.get_coherence_per_topic()
            lda_coherence = {i: score for i, score in enumerate(coherence_per_topic)}
            
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

    return templates.TemplateResponse("pages/search.html", {
        "request": request, 
        "results": results_dict, 
        "query": q,
        "lda_topics": lda_topics, 
        "bert_topics": bert_topics,
        "lda_coherence": lda_coherence
    })

@router.get("/api/search")
async def api_search(
    query: str = Query(..., min_length=2),
    conn = Depends(get_async_db),
    model = Depends(get_nlp_model)
):
    """
    Pure JSON Retrieval: Optimized for the RAG Chat Engine.
    """
    heart = RAGHeart(conn, model)
    results, _ = await heart.search(query)
    
    # Quick thematic discovery
    training_data = [r[1] for r in results]
    dynamic_k = max(1, min(5, len(training_data)))
    formatted = []
    
    if training_data:
        try:
            lda_topics, lda_model, dictionary = await anyio.to_thread.run_sync(
                get_topics, training_data, dynamic_k
            )
            bert_topics, bert_kmeans = await anyio.to_thread.run_sync(
                get_bert_topics, training_data, model, dynamic_k
            )
            
            for r in results:
                lda_id = await anyio.to_thread.run_sync(predict_topic, r[1], lda_model, dictionary)
                bert_id = await anyio.to_thread.run_sync(predict_bert_topic, r[1], model, bert_kmeans)
                
                # 1. Dynamic LDA Labels (Probabilistic)
                topic_words = lda_model.show_topic(lda_id, topn=10)
                lda_keywords_dict = {word: float(prob) for word, prob in topic_words}
                lda_label = ", ".join([word for word, _ in topic_words[:3]])
                
                # 2. Dynamic BERT Labels (Contextual)
                # bert_topics is a list of (id, keywords_string)
                bert_keywords_str = bert_topics[bert_id][1] if bert_id < len(bert_topics) else ""
                bert_keywords_list = [k.strip() for k in bert_keywords_str.split(",")]
                bert_label = ", ".join(bert_keywords_list[:3]) if bert_keywords_list else f"Context {bert_id + 1}"
                
                formatted.append({
                    "id": r[0], 
                    "content": r[1], 
                    "score": r[2],
                    "tag": f"LDA: {lda_label}",
                    "lda_topic_label": lda_label,
                    "bert_topic_label": bert_label,
                    "lda_keywords": lda_keywords_dict,
                    "bert_keywords": bert_keywords_list,
                    "created_at": r[4]
                })
        except Exception as e:
            print(f"⚠️ THEMATIC ERROR: {e}")
            import traceback
            traceback.print_exc()
            for r in results:
                formatted.append({"id": r[0], "content": r[1], "score": r[2], "tag": "Unprocessed", "created_at": r[4]})
    
    return {"results": formatted}
