# This is the manager of the hybrid search
from utils.console_stats import display_latency_report
import os
import time

from hybrid.HybridScorer import HybridScorer
from db.search_queries import execute_vector_query, execute_bm25_query

# Actual Utilities
from utils.ColorScheme import ColorScheme
from utils.helper_functions import check_if_empty_input, measure_time
from utils.rich_console import display_in_table
from utils.console_stats import display_search_stats

cs = ColorScheme()

try:
    BASE_THRESHOLD = float(os.environ.get("BASE_THRESHOLD", "0.15"))
except Exception:
    BASE_THRESHOLD = 0.15

try:
    TOP_K = int(os.environ.get("TOP_K", "5"))
except Exception:
    TOP_K = 5

def search_hybrid(
    query: str, conn, cursor, model, top_k=TOP_K, threshold=BASE_THRESHOLD, fusion_strategy="linear", alpha=None
):
    """
    Executes a hybrid search combining Semantic (Vector) and Lexical (BM25) results
    with high-precision latency tracking.
    """
    if check_if_empty_input(query):
        print(f"{cs.RED}Input cannot be empty.{cs.RESET}")
        return [], {}

    metrics = {}
    
    # 1. Semantic Search (The "Brain")
    start_sem = time.perf_counter()
    try:
        sem_results = execute_vector_query(query, conn, cursor, model, top_k, threshold)
    except Exception as e:
        print(f"{cs.RED}Error in execute_vector_query: {e}{cs.RESET}")
        sem_results = []
    metrics['semantic_ms'] = (time.perf_counter() - start_sem) * 1000

    # 2. BM25 Search (The "Muscle")
    start_key = time.perf_counter()
    try:
        bm25_results = execute_bm25_query(query, cursor, top_k)
    except Exception as e:
        print(f"{cs.RED}Error in execute_bm25_query: {e}{cs.RESET}")
        bm25_results = []
    metrics['keyword_ms'] = (time.perf_counter() - start_key) * 1000

    # Determine alpha (BM25 weight)
    if alpha is not None:
        try:
            ALPHA = float(alpha)
        except (ValueError, TypeError):
            ALPHA = 0.5
    else:
        try:
            alpha_val = os.environ.get("BM25_WEIGHT")
            if alpha_val is not None and alpha_val.strip() != "":
                ALPHA = float(alpha_val)
            else:
                sem_w = os.environ.get("SEMANTIC_WEIGHT")
                if sem_w is not None and sem_w.strip() != "":
                    ALPHA = max(0.0, min(1.0, 1.0 - float(sem_w)))
                else:
                    ALPHA = 0.5
        except Exception:
            ALPHA = 0.5

    # 3. Fusion Logic (The "Magic")
    start_fuse = time.perf_counter()
    try:
        scorer = HybridScorer(alpha=ALPHA)
        final, components = scorer.combine(sem_results, bm25_results, top_k=top_k, strategy=fusion_strategy)
    except Exception as e:
        print(f"{cs.RED}Error in HybridScorer: {e}{cs.RESET}")
        final, components = [], {}
    metrics['fusion_ms'] = (time.perf_counter() - start_fuse) * 1000

    # Finalize Metrics
    metrics['total_ms'] = sum(metrics.values())

    display_mode = "hybrid" if fusion_strategy == "linear" else f"hybrid-{fusion_strategy}"
    
    
    display_in_table(final, query=query, mode=display_mode, components=components) # This is the muscle of our search: BM25 is the "Muscle": It finds exact keywords (e.g., searching "pet" finds "pet").
    display_latency_report(metrics) # This is the brain of our search: Semantic Search is the "Brain": It finds meaning (e.g., searching "pet" finds "dog").
    
    stats = {
        "sem_results": sem_results,
        "bm25_results": bm25_results,
        "components": components,
        "alpha": ALPHA,
        "search_type": display_mode,
        "latency_stats": metrics
    }

    return final, stats

