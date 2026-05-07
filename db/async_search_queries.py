import math

async def execute_async_vector_query(query, conn, model, top_k, threshold):
    """
    Executes raw semantic (vector) search query asynchronously using asyncpg.
    """
    try:
        # 1. Model Encoding (Blocking, but usually small for single queries. 
        # For pure async, we'd use a threadpool, but here we'll keep it simple)
        query_vec = model.encode(query, show_progress_bar=False)

        if query_vec is None or len(query_vec) == 0:
            return []

        clean_vec = [float(0.0 if (math.isnan(v) or math.isinf(v)) else v) for v in query_vec.tolist()]
        vec_str = f"[{','.join(map(str, clean_vec))}]"
        
        sql = """
            SELECT 
                d.id, 
                d.content, 
                (1 - (e.embedding <=> $1::vector)) AS similarity,
                d.language, 
                d.created_at
            FROM document d
            INNER JOIN document_embedding e ON d.id = e.doc_id
            WHERE (1 - (e.embedding <=> $1::vector)) >= $2
            ORDER BY similarity DESC
            LIMIT $3
        """
        
        rows = await conn.fetch(sql, vec_str, threshold, top_k * 2)
        
        results = []
        for row in rows:
            results.append((row['id'], row['content'] or "", float(row['similarity']), row['language'] or "en", row['created_at']))
        
        return results
        
    except Exception as e:
        print(f"Error in execute_async_vector_query: {str(e)}")
        return []

async def execute_async_bm25_query(query, conn, top_k):
    """
    Executes raw BM25 (keyword) search query asynchronously using asyncpg.
    """
    try:
        sql = """
            SELECT d.id, d.content,
                   ts_rank(to_tsvector('english', d.content), plainto_tsquery('english', $1)) AS rank,
                   d.language, d.created_at
            FROM document d
            WHERE to_tsvector('english', d.content) @@ plainto_tsquery('english', $1)
              AND ts_rank(to_tsvector('english', d.content), plainto_tsquery('english', $1)) > 0.1
            ORDER BY rank DESC
            LIMIT $2
        """
        rows = await conn.fetch(sql, query, top_k)
        
        results = []
        for row in rows:
            results.append((row['id'], row['content'] or "", float(row['rank']), row['language'] or "en", row['created_at']))
        
        return results
    except Exception as e:
        print(f"Error in execute_async_bm25_query: {str(e)}")
        return []
