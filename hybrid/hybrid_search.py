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
    Executes a hybrid search combining Semantic (Vector) and Lexical (BM25) results.
    """
    if check_if_empty_input(query):
        print(f"{cs.RED}Input cannot be empty.{cs.RESET}")
        return [], {}
    
    get_elapsed = measure_time()
    t_start = time.time()

    # 1. Semantic Search
    try:
        sem_results = execute_vector_query(query, conn, cursor, model, top_k, threshold)
    except Exception as e:
        print(f"{cs.RED}Error in execute_vector_query: {e}{cs.RESET}")
        sem_results = []
    
    t_sem = time.time()
    
    # 2. BM25 Search (DB-Native TS_RANK)
    try:
        bm25_results = execute_bm25_query(query, cursor, top_k)
    except Exception as e:
        print(f"{cs.RED}Error in execute_bm25_query: {e}{cs.RESET}")
        bm25_results = []
        
    t_key = time.time()

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

    # 3. Fusion Logic
    try:
        scorer = HybridScorer(alpha=ALPHA)
        final, components = scorer.combine(sem_results, bm25_results, top_k=top_k, strategy=fusion_strategy)
    except Exception as e:
        print(f"{cs.RED}Error in HybridScorer: {e}{cs.RESET}")
        final, components = [], {}
        
    t_fuse = time.time()

    # Calculate Latency Breakdown
    lat_sem = (t_sem - t_start) * 1000
    lat_key = (t_key - t_sem) * 1000
    lat_fuse = (t_fuse - t_key) * 1000

    display_mode = "hybrid" if fusion_strategy == "linear" else f"hybrid-{fusion_strategy}"
    
    # Display results
    display_in_table(final, query=query, mode=display_mode)
    display_search_stats(sem_results, bm25_results, get_elapsed, mode=display_mode)

    stats = {
        "sem_results": sem_results,
        "bm25_results": bm25_results,
        "components": components,
        "alpha": ALPHA,
        "search_type": display_mode,
        "latency_stats": {
            "semantic": lat_sem,
            "keyword": lat_key,
            "fusion": lat_fuse
        }
    }

    return final, stats
