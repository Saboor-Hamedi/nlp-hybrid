import os
import httpx
from typing import List, Dict, Any

class DeepSeekClient:
    """
    Forensic Generator: Orchestrates communication with the DeepSeek LLM
    for synthesized research briefings.
    """
    
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        # DeepSeek often requires /v1 for OpenAI-compatible endpoints
        self.base_url = "https://api.deepseek.com/v1" 
        
    async def synthesize(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """
        Generates a synthesized forensic briefing based on retrieved records.
        """
        if not self.api_key:
            return "Neural Error: DEEPSEEK_API_KEY missing in environment."

        # Construct Forensic Context
        context_text = "\n\n".join([
            f"--- RECORD ID: {doc['id']} ---\n{doc['content']}" 
            for doc in context_docs
        ])

        system_prompt = (
            "You are a Forensic Research Assistant in the Neural Forensic Suite. "
            "Your task is to synthesize findings from the provided research records. "
            "1. Only use the provided context to answer. "
            "2. Be concise, industrial, and professional. "
            "3. Cite records by their ID (e.g., [ID: 101]). "
            "4. If the context does not contain the answer, state that forensic data is insufficient."
        )

        user_prompt = f"RESEARCH QUERY: {query}\n\nFORENSIC CONTEXT:\n{context_text}"

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key.strip()}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.2,
                        "max_tokens": 1500
                    }
                )
                
                # Capture and log raw response for debugging
                if response.status_code != 200:
                    print(f"🔥 DEEPSEEK CORE ERROR [{response.status_code}]: {response.text}")
                    return f"Neural Core Error: API returned {response.status_code}. Check server logs."
                
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"🔥 NEURAL CORE CRITICAL FAILURE: {str(e)}")
            return f"Neural Core Critical Failure: {str(e)}"
