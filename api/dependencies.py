from fastapi import Request, HTTPException
from db.db_connection import db_connection, get_model
from fastapi.templating import Jinja2Templates

# Global Jinja2 Template Engine
templates = Jinja2Templates(directory="templates")

from db.db_connection import db_connection, get_db_pool, get_model

async def get_async_db():
    """Dependency to yield an asyncpg connection from the pool."""
    pool = await get_db_pool()
    if not pool:
        raise HTTPException(status_code=500, detail="Database pool initialization failed.")
    async with pool.acquire() as connection:
        yield connection

def get_db():
    """Dependency to yield a database connection and guarantee cleanup."""
    conn = db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed.")
    try:
        yield conn
    finally:
        conn.close()

def get_nlp_model():
    """Dependency to fetch the singleton sentence transformer model."""
    model = get_model()
    if not model:
        raise HTTPException(status_code=500, detail="Model initialization failed.")
    return model
