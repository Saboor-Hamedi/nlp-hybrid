import asyncio
import os
import asyncpg
from dotenv import load_dotenv

async def test():
    load_dotenv()
    print(f"Connecting to {os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}...")
    try:
        conn = await asyncpg.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        print("✅ Connection successful!")
        await conn.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())
