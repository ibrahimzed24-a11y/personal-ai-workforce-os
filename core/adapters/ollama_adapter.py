import time
import logging
import httpx
from typing import Dict, Any, List, Optional
from core.adapters.base import ModelProvider

logger = logging.getLogger("ai_workforce_os.adapters.ollama")

class OllamaProvider(ModelProvider):
    """
    Local inference adapter for Ollama.
    Communicates via Ollama's local REST API (http://localhost:11434).
    """
    def __init__(self, base_url: str = "http://localhost:11434", model_name: str = "llama3.2:latest", timeout_seconds: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout = timeout_seconds
        self.provider_id = "local_ollama"

    async def check_health(self) -> Dict[str, Any]:
        """Check if local Ollama daemon is reachable and list installed models."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    return {
                        "status": "healthy",
                        "available": True,
                        "models": models,
                        "model_count": len(models)
                    }
                return {"status": "error", "available": False, "http_status": resp.status_code}
        except httpx.ConnectError:
            return {"status": "unreachable", "available": False, "message": f"Ollama daemon not reachable at {self.base_url}"}
        except Exception as e:
            return {"status": "error", "available": False, "message": str(e)}

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Dict[str, Any],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": context.get("temperature", 0.2)
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
                content = data.get("message", {}).get("content", "")
                prompt_tokens = data.get("prompt_eval_count", 0)
                eval_tokens = data.get("eval_count", 0)
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0

                return {
                    "content": content,
                    "parsed_json": None,
                    "provider": "local_ollama",
                    "model": self.model_name,
                    "classification": "local",
                    "usage": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": eval_tokens,
                        "total_tokens": prompt_tokens + eval_tokens
                    },
                    "latency_ms": elapsed_ms,
                    "raw": data
                }
            except httpx.ConnectError as e:
                logger.error(f"Failed to connect to local Ollama at {self.base_url}: {e}")
                raise ConnectionError(f"Ollama local inference server is unreachable at {self.base_url}. Ensure 'ollama serve' is running.")
            except Exception as e:
                logger.error(f"Ollama generation error: {e}")
                raise
