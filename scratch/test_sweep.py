
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
        print("Testing clean_garbage_modular...")
        # Test with simple string
        res = await conn.fetchval("SELECT clean_garbage_modular('Test [1] (Author, 2023)', true, true, true, true)")
        print(f"Result: '{res}'")
    except Exception as e:
        print(f"FAILURE: {repr(e)}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_db())
