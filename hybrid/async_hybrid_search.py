import os
import time
from hybrid.HybridScorer import HybridScorer
from db.async_search_queries import execute_async_vector_query, execute_async_bm25_query
from utils.ColorScheme import ColorScheme
from utils.helper_functions import check_if_empty_input
from utils.rich_console import display_in_table
from utils.console_stats import display_latency_report

cs = ColorScheme()

try:
    BASE_THRESHOLD = float(os.environ.get("BASE_THRESHOLD", "0.15"))
    TOP_K = int(os.environ.get("TOP_K", "5"))
except Exception:
    BASE_THRESHOLD = 0.15
    TOP_K = 5

async def search_hybrid_async(
    query: str, conn, model, top_k=TOP_K, threshold=BASE_THRESHOLD, fusion_strategy="linear", alpha=None
):
    if check_if_empty_input(query):
        return [], {}

    metrics = {}
    
    # 1. Semantic Search (The "Brain")
    start_sem = time.perf_counter()
    sem_results = await execute_async_vector_query(query, conn, model, top_k, threshold)
    metrics['semantic_ms'] = (time.perf_counter() - start_sem) * 1000

    # 2. BM25 Search (The "Muscle")
    start_key = time.perf_counter()
    bm25_results = await execute_async_bm25_query(query, conn, top_k)
    metrics['keyword_ms'] = (time.perf_counter() - start_key) * 1000

    # Determine alpha
    if alpha is not None:
        try: ALPHA = float(alpha)
        except: ALPHA = 0.5
    else:
        ALPHA = float(os.environ.get("BM25_WEIGHT", "0.5"))

    # 3. Fusion Logic
    start_fuse = time.perf_counter()
    scorer = HybridScorer(alpha=ALPHA)
    final, components = scorer.combine(sem_results, bm25_results, top_k=top_k, strategy=fusion_strategy)
    metrics['fusion_ms'] = (time.perf_counter() - start_fuse) * 1000

    metrics['total_ms'] = sum(metrics.values())
    
    stats = {
        "sem_results": sem_results,
        "bm25_results": bm25_results,
        "components": components,
        "alpha": ALPHA,
        "latency_stats": metrics
    }

    return final, stats
