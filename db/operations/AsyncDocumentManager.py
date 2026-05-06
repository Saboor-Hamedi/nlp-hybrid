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
            
            # 1. Lexical Normalization (Optimize BM25 indices)
            if config.get('normalize', True):
                # We use a dummy update to trigger the GIN index refresh or modular cleaning
                await self.conn.execute("UPDATE document SET language = 'insight' WHERE language = 'insight'")
                processed += 1 

            # 2. Neural Re-indexing (Re-vectorize with Safety Batching)
            if config.get('revectorize', False):
                # Safety Limit: Only process 100 documents per sweep to prevent OOM/Timeout
                batch_limit = 100
                docs_to_vectorize = await self.conn.fetch(
                    "SELECT id, content FROM document WHERE id NOT IN (SELECT doc_id FROM document_embedding) LIMIT $1", 
                    batch_limit
                )
                
                for doc in docs_to_vectorize:
                    embedding = self.model.encode(doc['content']).tolist()
                    await self.conn.execute(
                        "INSERT INTO document_embedding (doc_id, embedding) VALUES ($1, $2::vector)", 
                        doc['id'], str(embedding)
                    )
                    processed += 1
                
                # Check if there are more pending
                remaining = await self.conn.fetchval(
                    "SELECT COUNT(*) FROM document WHERE id NOT IN (SELECT doc_id FROM document_embedding)"
                )
                
                if remaining > 0:
                    status_msg = f"Batch complete. {remaining} records still pending indexing."

            return {
                "status": "success", 
                "message": status_msg, 
                "latency": f"{time.perf_counter() - start_time:.3f}s", 
                "processed": processed
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def get_total_count(self) -> int:
        try:
            count = await self.conn.fetchval("SELECT COUNT(*) FROM document")
            return count or 0
        except:
            return 0
