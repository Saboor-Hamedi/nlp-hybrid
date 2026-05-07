import os
from typing import List, Dict, Any, AsyncGenerator
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.core.llms import ChatMessage
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.llms.openai import OpenAI
from llama_index.core.llms.mock import MockLLM
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.memory import ChatMemoryBuffer

from utils.llm.deepseek_client import DeepSeekClient

class LlamaIndexMind:
    """
    Singleton Orchestrator for IndexOllam.
    Bridges LlamaIndex retrieval with the robust DeepSeekClient.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LlamaIndexMind, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, conn_str=None):
        if self._initialized:
            return
            
        # 1. Configuration
        db_user = os.getenv("DB_USER")
        db_pass = os.getenv("DB_PASSWORD")
        db_host = os.getenv("DB_HOST", "127.0.0.1")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME")
        
        # 2. Robust DeepSeek Client (Restored)
        self.ds_client = DeepSeekClient()
        
        # 3. Shared Embedding Model
        self.embed_model = HuggingFaceEmbedding(
            model_name=os.getenv("EMBEDDER_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
        )
        
        # 4. Hierarchical Node Parsing (Smart Context)
        from llama_index.core.node_parser import HierarchicalNodeParser, get_leaf_nodes
        
        # Create small chunks (128) for precision retrieval, 
        # and large chunks (1024) for robust LLM context.
        self.node_parser = HierarchicalNodeParser.from_defaults(
            chunk_sizes=[1024, 512, 128]
        )
        
        Settings.llm = MockLLM() 
        Settings.embed_model = self.embed_model
        Settings.node_parser = self.node_parser
        
        # 4. Persistent Vector Store
        self.vector_store = PGVectorStore.from_params(
            database=db_name,
            host=db_host,
            password=db_pass,
            port=db_port,
            user=db_user,
            table_name="forensic_index",
            embed_dim=384,
            schema_name="public"
        )
        
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        self.index = VectorStoreIndex.from_vector_store(
            self.vector_store, 
            storage_context=self.storage_context
        )
        
        # 5. Persistent Memory
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=3000)
        self._initialized = True
        print("🧠 IndexOllam - Neural Brain initialized and persistent.")

    def get_retriever(self):
        """
        Auto-Merging Retriever: Reconstructs fragmented chunks into robust dossiers.
        """
        from llama_index.core.retrievers import AutoMergingRetriever
        
        # Base retriever on the leaf nodes (small chunks)
        base_retriever = self.index.as_retriever(
            similarity_top_k=10 # Higher k for merging potential
        )
        
        return AutoMergingRetriever(
            base_retriever, 
            self.storage_context, 
            verbose=True
        )

    async def synthesize_stream(self, query: str, context_docs: List[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """
        High-performance streaming interface with robust error handling.
        """
        try:
            # 1. Pulse: Stops browser timeout
            yield " " 

            # 2. Conversational Bypass: Instant social response
            social_queries = ["hello", "hi", "hey", "how are you", "how's it going", "who are you", "help", "thanks", "thank you", "good morning", "good afternoon"]
            clean_query = query.lower().strip("?!. ")
            
            if clean_query in social_queries:
                messages = [
                    ChatMessage(role="system", content="You are a helpful, brief assistant. Respond like ChatGPT. Keep it to one short sentence."),
                    ChatMessage(role="user", content=query)
                ]
                # Directly using ds_client to bypass the 'Global Core' prompt
                async for token in self.ds_client.synthesize_stream(query, [], mode="global"):
                    yield token
                return

            # 3. Neural Retrieval (LlamaIndex)
            retriever = self.get_retriever()
            nodes = await retriever.aretrieve(query)
            
            # 4. Format context for the legacy synthesizer
            neural_context = [
                {"id": node.metadata.get("doc_id", "???"), "content": node.get_content()} 
                for node in nodes
            ]
            
            # Combine manual frontend context with neural retrieval
            final_context = (context_docs or []) + neural_context

            # 5. Execute Synthesis via the restored DeepSeekClient
            async for token in self.ds_client.synthesize_stream(query, final_context, mode="local"):
                yield token

        except Exception as e:
            print(f"🔥 NEURAL RESTORATION ERROR: {str(e)}")
            yield f"\n\n[SYSTEM RECOVERY ERROR: {str(e)}]\n\nPlease try again in 5 seconds."
