import os
import asyncpg
import psycopg2
from dotenv import load_dotenv
from models.ai_model import get_embedder

# Load environment variables
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
dotenv_path = os.path.join(base_dir, ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

class Database:
    """
    The central database and neural model hub for the Signal Forensic Suite.
    Manages the asyncpg pool and singleton AI model lifecycle.
    """
    _pool = None
    _model = None

    @classmethod
    async def get_pool(cls):
        """
        Returns a singleton asyncpg connection pool with auto-recovery logic.
        """
        if cls._pool is not None:
            if cls._pool.is_closing():
                cls._pool = None

        if cls._pool is None:
            try:
                db_host = os.getenv("DB_HOST", "127.0.0.1")
                if db_host == "localhost":
                    db_host = "127.0.0.1"
                
                cls._pool = await asyncpg.create_pool(
                    host=db_host,
                    port=int(os.getenv("DB_PORT", 5432)),
                    database=os.getenv("DB_NAME"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    min_size=2,
                    max_size=10,
                    command_timeout=60
                )
                print("✅ Industrial Database Pool Initialized.")
            except Exception as e:
                print(f"🔥 Pool Initialization Failure: {e}")
                return None
        return cls._pool

    @classmethod
    def get_model(cls):
        """
        Returns the singleton neural model for vector operations.
        """
        if cls._model is None:
            model_name = os.getenv("EMBEDDER_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
            cls._model = get_embedder(model_name)
            print(f"🧠 Neural Model [{model_name}] Initialized.")
        return cls._model

    @staticmethod
    def get_legacy_connection():
        """
        Provides a synchronous connection for legacy CLI operations (main.py).
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
            print(f"⚠️ Legacy Connection Failure: {e}")
            return None
