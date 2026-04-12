import math
import os

def execute_vector_query(query, conn, cursor, model, top_k, threshold):
    """
    Executes raw semantic (vector) search query against the database.
    """
    try:
        # 1. Model Encoding
        # query_vec = model.encode(query)
        query_vec = model.encode(query, show_progress_bar=False)

        if query_vec is None or len(query_vec) == 0:
            return []

        # 2. Convert to list and clean NaN/Inf values
        clean_vec = [float(0.0 if (math.isnan(v) or math.isinf(v)) else v) for v in query_vec.tolist()]
        
        # 3. Format vector as string for pgvector
        vec_str = f"[{','.join(map(str, clean_vec))}]"
        
        # 4. Execute SQL query
        sql = """
            SELECT 
                d.id, 
                d.content, 
                (1 - (e.embedding <=> %s::vector)) AS similarity,
                d.language, 
                d.created_at
            FROM document d
            INNER JOIN document_embedding e ON d.id = e.doc_id
            WHERE (1 - (e.embedding <=> %s::vector)) >= %s
            ORDER BY similarity DESC
            LIMIT %s
        """
        
        cursor.execute(sql, (vec_str, vec_str, threshold, top_k * 2))
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append((row[0], row[1] or "", float(row[2]), row[3] or "en", row[4]))
        
        return results
        
    except Exception as e:
        print(f"Error in execute_vector_query: {str(e)}")
        return []

def execute_bm25_query(query, cursor, top_k):
    """
    Executes raw BM25 (keyword) search query using PostgreSQL ts_rank.
    """
    try:
        cursor.execute("""
            SELECT d.id, d.content,
                   ts_rank(to_tsvector('english', d.content), plainto_tsquery('english', %s)) AS rank,
                   d.language, d.created_at
            FROM document d
            WHERE to_tsvector('english', d.content) @@ plainto_tsquery('english', %s)
            ORDER BY rank DESC
            LIMIT %s
        """, (query, query, top_k))

        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append((row[0], row[1] or "", float(row[2]), row[3] or "en", row[4]))
        
        return results
    except Exception as e:
        print(f"Error in execute_bm25_query: {str(e)}")
        return []
