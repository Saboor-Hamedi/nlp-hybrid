from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from api.dependencies import get_async_db, get_nlp_model, templates
from utils.analytics.topic_modeling import find_best_k, get_topics, plot_coherence, predict_topic, preprocess
from utils.analytics.bert_topic import get_bert_topics, predict_bert_topic
import anyio

router = APIRouter()

@router.get("/topics", response_class=HTMLResponse)
async def show_topics(request: Request, conn = Depends(get_async_db), model = Depends(get_nlp_model)):
    try:
        rows = await conn.fetch('SELECT id, content FROM document ORDER BY id DESC LIMIT 100')
        docs_data = [{"id": row['id'], "content": row['content']} for row in rows]

        if not docs_data:
            return "No documents found to analyze topics."

        # Process contents for modeling
        all_contents = [d['content'] for d in docs_data]

        # find_best_k and get_topics are CPU-bound
        best_k, coherence_scores = await anyio.to_thread.run_sync(find_best_k, all_contents, range(2, 7))
        await anyio.to_thread.run_sync(plot_coherence, coherence_scores, best_k)
        coherence_image = "/static/img/coherence_scores.png"

        lda_results, lda_model, dictionary = await anyio.to_thread.run_sync(get_topics, all_contents, best_k)
        bert_results, bert_kmeans = await anyio.to_thread.run_sync(get_bert_topics, all_contents, model, best_k)

        documents_with_tags = []
        for doc in docs_data[:50]:
            content = doc['content']
            lda_id = await anyio.to_thread.run_sync(predict_topic, content, lda_model, dictionary)
            bert_id = await anyio.to_thread.run_sync(predict_bert_topic, content, model, bert_kmeans)
            tokens = preprocess(content)
            documents_with_tags.append({
                "id": doc['id'],
                "content": content, "tokens": " ".join(tokens),
                "lda_tag": f"LDA {lda_id + 1}", "bert_tag": f"BERT {bert_id + 1}"
            })

        return templates.TemplateResponse("pages/topics.html", {
            "request": request, 
            "lda_topics": lda_results, 
            "bert_topics": bert_results,
            "documents": documents_with_tags, 
            "coherence_image": coherence_image,
            "coherence_scores": coherence_scores,
            "best_k": best_k
        })
    except Exception as e:
        return f"Error: {e}"
