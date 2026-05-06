from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from api.dependencies import get_async_db, templates
from utils.analytics.sentiment import get_sentiment_modeling
import anyio

router = APIRouter()

@router.get("/modeling", response_class=HTMLResponse)
async def show_modeling(request: Request, conn = Depends(get_async_db)):
    rows = await conn.fetch('SELECT content FROM document ORDER BY created_at DESC LIMIT 10')
    docs = [row['content'] for row in rows]

    if not docs:
        return "No documents found to analyze."

    sentiment_data = await anyio.to_thread.run_sync(get_sentiment_modeling, docs)
    
    # Calculate dynamic percentages for the UI
    total = len(docs)
    stats = {
        "pos_pct": (sentiment_data["positive"] / total) * 100 if total > 0 else 0,
        "neu_pct": (sentiment_data["neutral"] / total) * 100 if total > 0 else 0,
        "neg_pct": (sentiment_data["negative"] / total) * 100 if total > 0 else 0,
    }

    return templates.TemplateResponse("pages/modeling.html", {
        "request": request, 
        "sentiment": sentiment_data["details"], 
        "stats": stats,
        "total_docs": total
    })
