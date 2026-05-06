import time
from typing import List, Dict, Optional, Any
from asyncpg import Connection
from utils.ColorScheme import ColorScheme

class AsyncDocumentManager:
    """
    Handles asynchronous database operations for Document entities using asyncpg.
    """
    
    def __init__(self, conn: Connection, model: Any):
        """
        Initialize with an active asyncpg connection and an NLP model.
        """
        self.conn = conn
        self.model = model
        self.cs = ColorScheme()

    async def initialize_engine(self):
        """
        Automated Forensic Loader: Synchronizes database logic.
        """
        import os
        try:
            # Minimal migration: only clean_hash for differential sweep
            await self.conn.execute("ALTER TABLE document ADD COLUMN IF NOT EXISTS clean_hash TEXT DEFAULT '';")
            
            # Insights table for research tracking
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS forensic_insights (
                    id SERIAL PRIMARY KEY,
                    query TEXT NOT NULL,
                    content TEXT NOT NULL,
                    mode VARCHAR(20) DEFAULT 'local',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            async_dir = 'db/async'
            if os.path.exists(async_dir):
                sql_files = [f for f in os.listdir(async_dir) if f.endswith('.sql')]
                sql_files.sort()
                for filename in sql_files:
                    with open(os.path.join(async_dir, filename), 'r') as f:
                        sql_logic = f.read()
                    await self.conn.execute(sql_logic)
            
            print(f"{self.cs.BLUE}🧠 Neural Engine Synchronized.{self.cs.RESET}")
        except Exception as e:
            print(f"{self.cs.RED}❌ Engine Synchronization Failed: {e}{self.cs.RESET}")

    async def select(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        start_time = time.perf_counter()
        try:
            query = """
                SELECT d.id, d.content, d.language, d.created_at, e.embedding 
                FROM document d
                LEFT JOIN document_embedding e ON d.id = e.doc_id
                ORDER BY random() 
                LIMIT $1 OFFSET $2;
            """
            rows = await self.conn.fetch(query, limit, offset)
            results = [{
                "id": row['id'], "content": row['content'], "language": row['language'],
                "created_at": row['created_at'], "embedding": row['embedding']
            } for row in rows]
            return results
        except Exception as e:
            print(f"{self.cs.RED}❌ Async Select Error: {e}{self.cs.RESET}")
            return []

    async def show(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single document by its unique ID.
        """
        query = """
            SELECT d.id, d.content, d.language, d.created_at, e.embedding 
            FROM document d
            LEFT JOIN document_embedding e ON d.id = e.doc_id
            WHERE d.id = $1;
        """
        try:
            row = await self.conn.fetchrow(query, doc_id)
            if row: 
                return {
                    "id": row['id'],
                    "content": row['content'],
                    "language": row['language'],
                    "created_at": row['created_at'],
                    "embedding": row['embedding']
                }
            return None
        except Exception as e:
            print(f"{self.cs.RED}❌ Async Show Error: {e}{self.cs.RESET}")
            return None

    async def apply_forensic_sweep(self, config: Dict[str, bool]) -> Dict[str, Any]:
        """
        Industrial sweep: Handles both content normalization and neural re-indexing.
        """
        start_time = time.perf_counter()
        processed = 0
        
        try:
            status_msg = "Forensic cycle synchronized."
            
            # 1. Modular Forensic Cleaning (Batched)
            do_academic = config.get('academic', False)
            do_pdf = config.get('pdf', False)
            do_math = config.get('math', False)
            do_num = config.get('numerical', False)

            if any([do_academic, do_pdf, do_math, do_num]):
                try:
                    batch_limit = 100
                    print(f"🧹 Running batched modular cleaning (limit {batch_limit}): Acad={do_academic}, PDF={do_pdf}, Math={do_math}, Num={do_num}")
                    
                    res = await self.conn.execute("""
                        UPDATE document 
                        SET content = clean_garbage_modular(content, $1, $2, $3, $4)
                        WHERE id IN (
                            SELECT id FROM document 
                            WHERE content IS NOT NULL 
                            ORDER BY id ASC 
                            LIMIT $5
                        )
                    """, do_academic, do_pdf, do_math, do_num, batch_limit)
                    
                    # Extract count from "UPDATE N" status
                    cleaned_in_batch = int(res.split()[-1])
                    processed += cleaned_in_batch
                except Exception as clean_err:
                    print(f"❌ Modular Cleaning Failed: {repr(clean_err)}")
                    raise Exception(f"Cleaning phase failure: {repr(clean_err)}")

            # 2. Neural Re-indexing (Batched)
            if config.get('revectorize', False) or processed > 0:
                try:
                    reindex_limit = 50
                    print(f"🧠 Starting neural re-indexing batch (limit {reindex_limit})...")
                    docs_to_vectorize = await self.conn.fetch("""
                        SELECT id, content FROM document 
                        ORDER BY id ASC 
                        LIMIT $1
                    """, reindex_limit)
                    
                    for doc in docs_to_vectorize:
                        embedding = self.model.encode(doc['content']).tolist()
                        await self.conn.execute("DELETE FROM document_embedding WHERE doc_id = $1", doc['id'])
                        await self.conn.execute(
                            "INSERT INTO document_embedding (doc_id, embedding) VALUES ($1, $2::vector)", 
                            doc['id'], str(embedding)
                        )
                    
                    processed += len(docs_to_vectorize)
                    status_msg = f"Forensic sweep complete. Modular cleaning applied to {processed} records."
                except Exception as vector_err:
                    print(f"❌ Neural Re-indexing Failed: {repr(vector_err)}")
                    raise Exception(f"Re-indexing phase failure: {repr(vector_err)}")

            return {
                "status": "success", 
                "message": status_msg, 
                "latency": f"{time.perf_counter() - start_time:.3f}s", 
                "processed": processed
            }
        except Exception as e:
            print(f"🔥 Final Sweep Error: {repr(e)}")
            return {"status": "error", "message": repr(e)}

    async def get_total_count(self) -> int:
        try:
            count = await self.conn.fetchval("SELECT COUNT(*) FROM document")
            return count or 0
        except:
            return 0
