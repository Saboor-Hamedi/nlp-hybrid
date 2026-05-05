import os

import numpy as np
import psycopg2
from dotenv import load_dotenv

# Load environment variables explicitly from the advanced-nlp/.env file
try:
    # Adjusting base_dir to point to advanced-nlp/ where .env is located
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dotenv_path = os.path.join(base_dir, ".env")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
        print(f"Loaded environment from {dotenv_path}")
    else:
        # Fallback to default behavior (load first .env found)
        load_dotenv()
        print("No advanced-nlp/.env found; loaded default .env if present")
except Exception as e:
    print("Error loading .env:", e)

import asyncpg

_pool = None

async def get_db_pool():
    """
    Returns a singleton asyncpg connection pool with auto-recovery logic.
    """
    global _pool
    # Check if pool exists and is healthy
    if _pool is not None:
        # asyncpg internal check for closing/closed states
        if _pool.is_closing():
            print("🔄 Database pool is closing. Re-initializing...")
            _pool = None

    if _pool is None:
        try:
            db_host = os.getenv("DB_HOST", "127.0.0.1")
            if db_host == "localhost":
                db_host = "127.0.0.1"
                
            db_port = int(os.getenv("DB_PORT", 5432))
            
            _pool = await asyncpg.create_pool(
                host=db_host,
                port=db_port,
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            print("✅ Async database pool initialized.")
        except Exception as e:
            print(f"Error creating asyncpg pool: {e}")
            return None
    return _pool

def db_connection():
    """
    Creates and returns a connection to the PostgreSQL database using environment variables.
    """
    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )
    except Exception as e:
        print(f"Error connecting to PostgreSQL database. Details: {e}")
        return None

def get_db_cursor(conn):
    """
    Returns a cursor from the provided connection.
    """
    return conn.cursor() if conn else None

from models.ai_model import get_embedder

def get_model():
    """
    Delegates to the centralized get_embedder singleton.
    Uses 'EMBEDDER_MODEL' env var if available.
    """
    model_name = os.getenv("EMBEDDER_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
    return get_embedder(model_name)
