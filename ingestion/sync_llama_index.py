import asyncio
import os
from db.Database import Database
from hybrid.LlamaIndexMind import LlamaIndexMind
from llama_index.core import Document, Settings
from utils.ColorScheme import ColorScheme

cs = ColorScheme()

async def sync_forensic_data():
    """
    Synchronizes existing documents into the LlamaIndex 'IndexOllam' ecosystem.
    """
    print(f"\n{cs.CYAN}--- Signal Forensic Sync: Data Migration ---{cs.RESET}")
    
    # 1. Initialize DB and Orchestrator
    pool = await Database.get_pool()
    mind = LlamaIndexMind()
    
    async with pool.acquire() as conn:
        # 2. Fetch all raw documents
        print(f"{cs.BLUE}📡 Fetching raw documents from registry...{cs.RESET}")
        rows = await conn.fetch("SELECT id, content, language FROM document")
        
        if not rows:
            print(f"{cs.YELLOW}⚠️ No documents found to synchronize.{cs.RESET}")
            return

        print(f"{cs.BLUE}🧠 Converting {len(rows)} records to Neural Index format...{cs.RESET}")
        
        documents = []
        for row in rows:
            # We wrap the existing content in LlamaIndex Document objects
            doc = Document(
                text=row['content'],
                metadata={
                    "doc_id": row['id'],
                    "source": "legacy_registry",
                    "language": row['language'] or "en"
                }
            )
            documents.append(doc)

        # 3. Batched Ingestion into IndexOllam
        print(f"{cs.GREEN}🚀 Injecting data into IndexOllam (Forensic Index)...{cs.RESET}")
        
        batch_size = 500
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            nodes = Settings.node_parser.get_nodes_from_documents(batch)
            mind.index.insert_nodes(nodes)
            print(f"  {cs.BLUE}🔄 Processed {min(i + batch_size, len(documents))}/{len(documents)} records...{cs.RESET}")
        
        print(f"{cs.GREEN}✅ Synchronization Complete. {len(documents)} records are now conversational.{cs.RESET}")

if __name__ == "__main__":
    asyncio.run(sync_forensic_data())
