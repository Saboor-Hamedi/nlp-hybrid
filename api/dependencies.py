from db.Database import Database
from fastapi.templating import Jinja2Templates

# Global Jinja2 Template Engine
templates = Jinja2Templates(directory="templates")

async def get_async_db():
    """Dependency to yield an asyncpg connection from the pool via Database Hub."""
    pool = await Database.get_pool()
    if not pool:
        raise HTTPException(status_code=500, detail="Database pool initialization failed.")
    async with pool.acquire() as connection:
        yield connection

def get_db():
    """Legacy dependency to yield a sync connection (only for legacy components)."""
    conn = Database.get_legacy_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed.")
    try:
        yield conn
    finally:
        conn.close()

def get_nlp_model():
    """Dependency to fetch the singleton sentence transformer model from Database Hub."""
    model = Database.get_model()
    if not model:
        raise HTTPException(status_code=500, detail="Model initialization failed.")
    return model
