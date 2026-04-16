

"""
 - This class is the judge. 
 - This is where the math happens.
 - This is where the magic happens. 
 - This is where the final score is calculated. 
 - This is sophistica, but not really it can go way more sophisticated.
"""
import math
import os
from typing import Any, Dict, List, Tuple

class HybridScorer:
    """Encapsulates hybrid scoring logic: normalize scores, combine with different strategies.
    
    Strategies:
    - 'linear': alpha * BM25 + (1-alpha) * Semantic
    - 'combsum': Sum of normalized scores
    - 'combmnz': CombSUM * (number of non-zero sources)
    """

    def __init__(self, alpha: float = 0.5):
        if not 0.0 <= alpha <= 1.0:
            raise ValueError("alpha must be between 0 and 1")
        self.alpha = float(alpha)

    
    """
        This function is the most important part of this file. 
        It takes a list of scores and squashes them into a range of 0 to 1.
    """

    def _normalize_values(self, scores: List[float], method: str = "max") -> List[float]:
        if not scores:
            return []
        
        min_s, max_s = min(scores), max(scores)
        
        if method == "log":
            denom = math.log1p(max_s) if max_s > 0 else 1.0
            return [(math.log1p(s) / denom) if max_s > 0 else 0.0 for s in scores]

        if method == "minmax":
            denom = max_s - min_s if max_s != min_s else 1.0
            return [(s - min_s) / denom if max_s != min_s else (1.0 if s > 0 else 0.0) for s in scores]

        denom = max_s if max_s > 0 else 1.0
        return [(s / denom) if denom > 0 else 0.0 for s in scores]

    def combine(
        self,
        sem_results: List[Tuple],
        bm25_results: List[Tuple],
        top_k: int = 10,
        strategy: str = "linear"
    ):
        bm25_method = os.getenv("HYBRID_BM25_NORM", "max").strip().lower()
        if strategy in ["combsum", "combmnz"]:
            bm25_method = "max"
            
        bm25_scores_raw = [r[2] for r in bm25_results]
        bm25_scores_norm = self._normalize_values(bm25_scores_raw, bm25_method)
        bm25_map = {r[0]: s for r, s in zip(bm25_results, bm25_scores_norm)}

        sem_scores_raw = [r[2] for r in sem_results]
        sem_scores_norm = self._normalize_values(sem_scores_raw, "max")
        sem_map = {r[0]: s for r, s in zip(sem_results, sem_scores_norm)}
        
        sem_ranks = {r[0]: i+1 for i, r in enumerate(sem_results)}
        bm25_ranks = {r[0]: i+1 for i, r in enumerate(bm25_results)}

        all_ids = set(bm25_map.keys()) | set(sem_map.keys())
        
        content_lookup = {}
        for r in sem_results: content_lookup[r[0]] = (r[1], r[3], r[4])
        for r in bm25_results: 
            if r[0] not in content_lookup:
                content_lookup[r[0]] = (r[1], None, None)

        result_map = {}

        for doc_id in all_ids:
            s_norm = sem_map.get(doc_id, 0.0)
            b_norm = bm25_map.get(doc_id, 0.0)
            
            if strategy == "combsum":
                score = s_norm + b_norm
            elif strategy == "combmnz":
                count = (1 if s_norm > 1e-6 else 0) + (1 if b_norm > 1e-6 else 0)
                score = (s_norm + b_norm) * count
            else:
                score = (b_norm * self.alpha) + (s_norm * (1 - self.alpha))

            content, lang, created = content_lookup.get(doc_id, (None, None, None))
            
            result_map[doc_id] = {
                "content": content,
                "language": lang,
                "created_at": created,
                "semantic_score": s_norm,
                "bm25_score": b_norm,
                "final_score": score
            }

        final_list = []
        components = {}
        
        for doc_id, v in result_map.items():
            final_list.append((doc_id, v["content"], float(v["final_score"]), v["language"], v["created_at"]))
            components[doc_id] = {
                "semantic_score": v["semantic_score"],
                "bm25_score": v["bm25_score"],
                "semantic_rank": sem_ranks.get(doc_id),
                "bm25_rank": bm25_ranks.get(doc_id),
                "semantic_weight": 1 - self.alpha if strategy == "linear" else 1.0,
                "bm25_weight": self.alpha if strategy == "linear" else 1.0,
                "strategy": strategy
            }

        final_sorted = sorted(final_list, key=lambda x: x[2], reverse=True)[:top_k]
        return final_sorted, components
