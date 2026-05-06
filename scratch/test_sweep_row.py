
import asyncio
import os
import asyncpg
from dotenv import load_dotenv

async def test_db():
    load_dotenv()
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    if db_host == "localhost": db_host = "127.0.0.1"
    
    conn = await asyncpg.connect(
        host=db_host,
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    
    try:
        print("Testing UPDATE on 1 row...")
        res = await conn.execute("UPDATE document SET content = clean_garbage_modular(content, true, true, true, true) WHERE id = (SELECT id FROM document LIMIT 1)")
        print(f"Update status: {res}")
    except Exception as e:
        print(f"FAILURE: {repr(e)}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_db())
