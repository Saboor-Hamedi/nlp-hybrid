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

    async def select(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Fetch a list of documents with random ordering for discovery.
        """
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
            
            results = [
                {
                    "id": row['id'],
                    "content": row['content'],
                    "language": row['language'],
                    "created_at": row['created_at'],
                    "embedding": row['embedding']
                }
                for row in rows
            ]
            
            elapsed = time.perf_counter() - start_time
            print(f"{self.cs.GREEN}✅ Async Selected {len(results)} docs ({elapsed:.3f}s){self.cs.RESET}")
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

    async def get_total_count(self) -> int:
        """
        Get the total count of documents in the repository.
        """
        try:
            count = await self.conn.fetchval("SELECT COUNT(*) FROM document")
            return count or 0
        except Exception as e:
            print(f"{self.cs.RED}❌ Error fetching total count: {e}{self.cs.RESET}")
            return 0
