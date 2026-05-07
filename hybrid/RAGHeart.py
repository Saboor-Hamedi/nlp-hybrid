import os
import time
from hybrid.HybridScorer import HybridScorer
from db.async_search_queries import execute_async_vector_query, execute_async_bm25_query
from utils.helper_functions import check_if_empty_input

class RAGHeart:
    """
    The central engine for hybrid forensic retrieval.
    Orchestrates semantic (vector) and lexical (BM25) search with high-fidelity fusion.
    """
    def __init__(self, conn, model, alpha=None):
        self.conn = conn
        self.model = model
        
        # Initialize configuration from environment with industrial defaults
        try:
            self.base_threshold = float(os.environ.get("BASE_THRESHOLD", "0.15"))
            self.top_k = int(os.environ.get("TOP_K", "5"))
            self.alpha = float(alpha) if alpha is not None else float(os.environ.get("BM25_WEIGHT", "0.5"))
        except Exception:
            self.base_threshold = 0.15
            self.top_k = 5
            self.alpha = 0.5

    async def search(self, query: str, top_k=None, threshold=None, strategy="rrf"):
        """
        Execute a synchronized hybrid search across semantic and lexical planes.
        Returns a tuple of (final_results, performance_metrics).
        """
        if check_if_empty_input(query):
            return [], {}

        k = top_k or self.top_k
        t = threshold or self.base_threshold
        metrics = {}

        # 1. Semantic Search (The "Brain") - Vector-space similarity
        start_sem = time.perf_counter()
        sem_results = await execute_async_vector_query(query, self.conn, self.model, k, t)
        metrics['semantic_ms'] = (time.perf_counter() - start_sem) * 1000

        # 2. BM25 Search (The "Muscle") - Lexical keyword matching
        start_key = time.perf_counter()
        bm25_results = await execute_async_bm25_query(query, self.conn, k)
        metrics['keyword_ms'] = (time.perf_counter() - start_key) * 1000

        # 3. Fusion Logic (The "Core") - Linear weighting and normalization
        start_fuse = time.perf_counter()
        scorer = HybridScorer(alpha=self.alpha)
        final, components = scorer.combine(sem_results, bm25_results, top_k=k, strategy=strategy)
        metrics['fusion_ms'] = (time.perf_counter() - start_fuse) * 1000

        metrics['total_ms'] = sum(metrics.values())
        
        # Forensic Intelligence Package
        intelligence = {
            "sem_results": sem_results,
            "bm25_results": bm25_results,
            "components": components,
            "alpha": self.alpha,
            "latency_stats": metrics
        }

        return final, intelligence
