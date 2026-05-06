import httpx
from fastapi import HTTPException
from utils.llm.deepseek_client import DeepSeekClient
from db.Database import Database

class RAGMind:
    """
    The intelligence orchestrator for the Signal Forensic Suite.
    Handles synthesis, text refinement, and insight archiving.
    """
    def __init__(self, conn):
        self.conn = conn
        self.llm = DeepSeekClient()
        
        # Centralized Forensic Prompt Registry
        self.prompts = {
            "refinement": (
                "You are a Forensic Research Assistant. Your task is to process or generate text "
                "based on the instruction: '{instruction}'. "
                "If text is provided, transform it. If no text is provided, generate a new forensic "
                "segment from scratch. Return ONLY the final text with no conversational filler."
            ),
            "synthesis": (
                "You are a Forensic Analyst orchestrating a Signal Synthesis. "
                "Based on the retrieved context, provide a high-density, authoritative briefing."
            )
        }

    async def synthesize_stream(self, query: str, context: list, mode: str = "local"):
        """
        Streaming interface for neural synthesis.
        """
        return self.llm.synthesize_stream(query, context, mode)

    async def refine(self, text: str, instruction: str = None):
        """
        Surgical text refinement using the neural engine.
        """
        if not instruction:
            instruction = "Clean the text: force lowercase and remove all symbols."

        system_prompt = self.prompts["refinement"].format(instruction=instruction)
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.llm.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.llm.api_key}"},
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": text}
                        ],
                        "temperature": 0.1
                    }
                )
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            raise Exception(f"Neural Refinement Failure: {str(e)}")

    async def archive_insight(self, query: str, content: str, mode: str = "local"):
        """
        Industrial Archiving: Commits insights to the registry and vector archive.
        """
        try:
            # 1. Commit to dedicated Forensic Registry
            await self.conn.execute(
                "INSERT INTO forensic_insights (query, content, mode) VALUES ($1, $2, $3)",
                query, content, mode
            )

            # 2. Integrate into the Main Searchable Archive
            doc_id = await self.conn.fetchval(
                "INSERT INTO document (content, language) VALUES ($1, 'insight') RETURNING id",
                content
            )

            # 3. Generate and Commit Neural Embedding
            model = Database.get_model()
            if not model:
                raise Exception("Neural Model not initialized for vectorization")
                
            embedding_list = model.encode(content).tolist()
            embedding_str = "[" + ",".join(map(str, embedding_list)) + "]"
            
            await self.conn.execute(
                "INSERT INTO document_embedding (doc_id, embedding) VALUES ($1, $2::vector)",
                doc_id, embedding_str
            )

            return doc_id
        except Exception as e:
            raise Exception(f"Forensic Archive Failure: {str(e)}")
