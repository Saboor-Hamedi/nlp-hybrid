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
        Automated Forensic Loader: Programmatically injects all modular logic 
        found in the db/async directory into the database.
        """
        import os
        try:
            # Migration: Ensure clean_hash exists for differential cleaning
            await self.conn.execute("ALTER TABLE document ADD COLUMN IF NOT EXISTS clean_hash TEXT DEFAULT '';")
            
            async_dir = 'db/async'
            if not os.path.exists(async_dir):
                print(f"{self.cs.RED}❌ Async Engine Directory Missing{self.cs.RESET}")
                return

            sql_files = [f for f in os.listdir(async_dir) if f.endswith('.sql')]
            # Sort to ensure orchestrator is loaded last (if needed, though not strictly required for creation)
            sql_files.sort() 

            for filename in sql_files:
                with open(os.path.join(async_dir, filename), 'r') as f:
                    sql_logic = f.read()
                await self.conn.execute(sql_logic)
            
            print(f"{self.cs.BLUE}🧠 Neural Engine Synchronized: {len(sql_files)} modules active.{self.cs.RESET}")
        except Exception as e:
            print(f"{self.cs.RED}❌ Engine Synchronization Failed: {e}{self.cs.RESET}")

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

    async def apply_forensic_sweep(self, config: Dict[str, bool]) -> Dict[str, Any]:
        """
        Execute a surgical differential forensic sweep.
        Only processes records that don't match the current cleaning configuration.
        """
        start_time = time.perf_counter()
        
        # Generate a unique "Forensic Signature" for the current settings
        config_signature = "-".join([
            f"A{int(config.get('academic', True))}",
            f"F{int(config.get('pdf', True))}",
            f"M{int(config.get('math', True))}",
            f"N{int(config.get('numerical', True))}"
        ])
        
        try:
            # 1. Identify how many records actually need processing
            pending_count = await self.conn.fetchval(
                "SELECT COUNT(*) FROM document WHERE clean_hash != $1", config_signature
            )
            
            if pending_count == 0:
                return {
                    "status": "success",
                    "message": "Archive is already synchronized with current calibration.",
                    "latency": f"{time.perf_counter() - start_time:.3f}s",
                    "processed": 0
                }

            # 2. Execute Surgical Strike
            query = """
                UPDATE document 
                SET content = clean_garbage_modular(content, $1, $2, $3, $4),
                    clean_hash = $5
                WHERE clean_hash != $5;
            """
            await self.conn.execute(
                query, 
                config.get('academic', True),
                config.get('pdf', True),
                config.get('math', True),
                config.get('numerical', True),
                config_signature
            )
            
            elapsed = time.perf_counter() - start_time
            return {
                "status": "success",
                "message": f"Surgical sweep complete. {pending_count} records re-calibrated.",
                "latency": f"{elapsed:.3f}s",
                "processed": pending_count
            }
        except Exception as e:
            print(f"{self.cs.RED}❌ Surgical Sweep Error: {e}{self.cs.RESET}")
            return {"status": "error", "message": str(e)}

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
