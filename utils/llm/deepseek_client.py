import os
import httpx
import json
from typing import List, Dict, Any, AsyncGenerator

class DeepSeekClient:
    """
    Forensic Generator: Orchestrates communication with the DeepSeek LLM
    for synthesized research briefings with streaming support.
    """
    
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.base_url = "https://api.deepseek.com/v1" 
        
    async def synthesize_stream(self, query: str, context_docs: List[Dict[str, Any]], mode: str = "local") -> AsyncGenerator[str, None]:
        """
        Generates a streaming synthesized briefing.
        """
        if not self.api_key:
            yield "Neural Error: DEEPSEEK_API_KEY missing."
            return

        if mode == "local":
            context_text = "\n\n".join([f"--- RECORD ID: {doc['id']} ---\n{doc['content']}" for doc in context_docs])
            system_prompt = (
                "You are a Forensic Research Assistant. Synthesize findings from provided records. "
                "1. Only use provided context. 2. Be concise. 3. Cite IDs like [ID: 101]. "
                "4. If context is missing, state 'insufficient data'."
            )
            user_prompt = f"RESEARCH QUERY: {query}\n\nFORENSIC CONTEXT:\n{context_text}"
        else:
            system_prompt = "You are the DeepSeek Global Intelligence Core. Provide high-fidelity, general-purpose intelligence."
            user_prompt = query

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key.strip()}", "Content-Type": "application/json"},
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                        "temperature": 0.2 if mode == "local" else 0.7,
                        "stream": True # Enable streaming
                    }
                ) as response:
                    if response.status_code != 200:
                        yield f"Neural Core Error: {response.status_code}"
                        return

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            if line.strip() == "data: [DONE]":
                                break
                            try:
                                chunk = json.loads(line[6:])
                                content = chunk["choices"][0]["delta"].get("content", "")
                                if content:
                                    yield content
                            except:
                                continue
        except Exception as e:
            yield f"Neural Core Critical Failure: {str(e)}"
