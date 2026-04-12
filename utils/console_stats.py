import os
import sys

# Ensure path is set correctly
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from typing import Any, Callable, List, Tuple

from utils.helper_functions import measure_time

from utils.ColorScheme import ColorScheme

cs = ColorScheme()


def display_search_stats(
    semantic_results: List[Tuple[Any, ...]],
    bm25_results: List[Tuple[Any, ...]],
    get_elapsed_func: Callable[[], str],
    mode: str = "semantic",                     # NEW – default keeps old behaviour
) -> None:
    """
    Prints CLI statistics regarding search results and elapsed time.

    Args:
        semantic_results: Results from the vector (semantic) search.
        bm25_results:    Results from the BM25 / FTS (keyword) search.
        get_elapsed_func: Callable that returns a formatted time string.
        mode:            One of "semantic", "keyword", or "hybrid".
                         Controls which label is printed.
    """
    # -----------------------------------------------------------------
    # 1. Semantic / Vector count
    # -----------------------------------------------------------------
    if mode in ("semantic", "hybrid"):
        print(f"{cs.GREEN}Semantic results: {len(semantic_results)} documents{cs.RESET}")

    # -----------------------------------------------------------------
    # 2. BM25 / Keyword count – only when we have a keyword component
    # -----------------------------------------------------------------
    if mode in ("keyword", "hybrid") and bm25_results:
        # Count only documents with a positive BM25 score
        positive = len([r for r in bm25_results if r[2] > 0])
        print(f"{cs.GREEN}BM25 results: {positive} documents with score > 0{cs.RESET}")
    elif mode == "keyword" and not bm25_results:
        print(f"{cs.GREEN}BM25 results: 0 documents{cs.RESET}")

    # -----------------------------------------------------------------
    # 3. Final timing line (always shown)
    # -----------------------------------------------------------------
    print(f"{cs.OKBLUE}Search complete. Time: {get_elapsed_func()}{cs.RESET}")


def display_latency_report(metrics):
    print(f"\n{cs.BOLD}⏱️  Latency Breakdown{cs.RESET}")
    print("-" * 30)
    for key, value in metrics.items():
        # Highlight slower parts in Red, fast parts in Green
        color = cs.RED if value > 500 else cs.GREEN 
        name = key.replace('_ms', '').capitalize()
        print(f"{name:<12} : {color}{value:>7.2f} ms{cs.RESET}")
    print("-" * 30)
