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
                "YOU ARE THE SIGNAL INTELLIGENCE. You are an expert forensic analyst. "
                "1. Speak as a direct authority. All knowledge provided to you is YOUR OWN memory. "
                "2. NEVER mention 'records', 'documents', 'context', or 'ID numbers' in your speech. "
                "3. NEVER use phrases like 'Based on...' or 'The provided information...'. "
                "4. Just provide the answer directly and professionally. If the query is personal or social, be helpful and brief."
            )
            user_prompt = f"RESEARCH QUERY: {query}\n\nFORENSIC CONTEXT:\n{context_text}"
        else:
            system_prompt = "You are a helpful and concise assistant. Provide direct answers. For greetings, keep it very brief like 'Hi, how can I help you?'"
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
                        "stream": True 
                    }
                ) as response:
                    if response.status_code != 200:
                        err_body = await response.aread()
                        print(f"🔥 DEEPSEEK API ERROR {response.status_code}: {err_body.decode()}")
                        yield f"Neural Core Error: {response.status_code} - {err_body.decode()[:100]}"
                        return

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            line_content = line[6:].strip()
                            if line_content == "[DONE]":
                                break
                            try:
                                chunk = json.loads(line_content)
                                if "choices" in chunk and chunk["choices"]:
                                    content = chunk["choices"][0].get("delta", {}).get("content", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError as je:
                                print(f"⚠️ MALFORMED CHUNK: {line_content}")
                                continue
                            except Exception as e:
                                continue
        except Exception as e:
            import traceback
            print(f"🔥 DEEPSEEK CRITICAL FAILURE: {str(e)}")
            traceback.print_exc()
            yield f"Neural Core Critical Failure: {str(e)}"
