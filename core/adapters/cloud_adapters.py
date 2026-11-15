import time
import logging
import httpx
from typing import Dict, Any, List, Optional
from core.adapters.base import ModelProvider

logger = logging.getLogger("ai_workforce_os.adapters.cloud")

class OpenAICompatibleProvider(ModelProvider):
    """
    HTTP provider for OpenAI-compatible endpoints.
    Compatible with OpenAI, OpenRouter, Groq, Together AI, vLLM, LM Studio, etc.
    """
    def __init__(
        self,
        base_url: str = "https://api.openai.com/v1",
        api_key: str = "",
        model_name: str = "gpt-4o",
        timeout_seconds: float = 60.0
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout_seconds
        self.provider_id = "cloud_openai"

    async def check_health(self) -> Dict[str, Any]:
        """Test API reachability and authentication."""
        if not self.api_key:
            return {"status": "unauthenticated", "available": False, "message": "API key not configured."}
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/models", headers=headers)
                if resp.status_code == 200:
                    return {"status": "healthy", "available": True}
                elif resp.status_code in (401, 403):
                    return {"status": "unauthenticated", "available": False, "message": "Invalid API credentials."}
                return {"status": "error", "available": False, "http_status": resp.status_code}
        except Exception as e:
            return {"status": "unreachable", "available": False, "message": str(e)}

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Dict[str, Any],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise PermissionError("OpenAI API key is missing. Configure via Vault or OS settings.")

        start_time = time.perf_counter()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": context.get("temperature", 0.2)
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            usage_raw = data.get("usage", {})
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            return {
                "content": content,
                "parsed_json": None,
                "provider": self.provider_id,
                "model": self.model_name,
                "classification": "cloud",
                "usage": {
                    "prompt_tokens": usage_raw.get("prompt_tokens", 0),
                    "completion_tokens": usage_raw.get("completion_tokens", 0),
                    "total_tokens": usage_raw.get("total_tokens", 0)
                },
                "latency_ms": elapsed_ms,
                "raw": data
            }

class GeminiProvider(ModelProvider):
    """
    Google Gemini Cloud Provider.
    Supports Gemini 1.5 Pro / Flash models via Google AI Studio API.
    """
    def __init__(
        self,
        api_key: str = "",
        model_name: str = "gemini-1.5-flash",
        timeout_seconds: float = 60.0
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout_seconds
        self.provider_id = "cloud_gemini"

    async def check_health(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"status": "unauthenticated", "available": False, "message": "Gemini API key not configured."}
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return {"status": "healthy", "available": True}
                return {"status": "unauthenticated", "available": False, "http_status": resp.status_code}
        except Exception as e:
            return {"status": "unreachable", "available": False, "message": str(e)}

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Dict[str, Any],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise PermissionError("Gemini API key is missing. Configure via Vault or OS settings.")

        start_time = time.perf_counter()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": context.get("temperature", 0.2)}
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            content = candidates[0]["content"]["parts"][0]["text"] if candidates else ""
            usage_meta = data.get("usageMetadata", {})
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            return {
                "content": content,
                "parsed_json": None,
                "provider": "cloud_gemini",
                "model": self.model_name,
                "classification": "cloud",
                "usage": {
                    "prompt_tokens": usage_meta.get("promptTokenCount", 0),
                    "completion_tokens": usage_meta.get("candidatesTokenCount", 0),
                    "total_tokens": usage_meta.get("totalTokenCount", 0)
                },
                "latency_ms": elapsed_ms,
                "raw": data
            }

class AnthropicProvider(ModelProvider):
    """
    Anthropic Claude Cloud Provider.
    Supports Claude 3.5 Sonnet / Haiku via the Anthropic Messages API.
    """
    def __init__(
        self,
        api_key: str = "",
        model_name: str = "claude-3-5-sonnet-20241022",
        timeout_seconds: float = 60.0
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout_seconds
        self.provider_id = "cloud_anthropic"

    async def check_health(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"status": "unauthenticated", "available": False, "message": "Anthropic API key not configured."}
        # Lightweight check: send a minimal request
        try:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json={"model": self.model_name, "max_tokens": 1, "messages": [{"role": "user", "content": "ping"}]}
                )
                if resp.status_code in (200, 400): # 400 is schema error but proves auth succeeded
                    return {"status": "healthy", "available": True}
                elif resp.status_code in (401, 403):
                    return {"status": "unauthenticated", "available": False, "message": "Invalid Anthropic API key."}
                return {"status": "error", "available": False, "http_status": resp.status_code}
        except Exception as e:
            return {"status": "unreachable", "available": False, "message": str(e)}

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Dict[str, Any],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise PermissionError("Anthropic API key is missing. Configure via Vault or OS settings.")

        start_time = time.perf_counter()
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "max_tokens": context.get("max_tokens", 4096),
            "temperature": context.get("temperature", 0.2)
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data.get("content", [{}])[0].get("text", "")
            usage_raw = data.get("usage", {})
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            return {
                "content": content,
                "parsed_json": None,
                "provider": "cloud_anthropic",
                "model": self.model_name,
                "classification": "cloud",
                "usage": {
                    "prompt_tokens": usage_raw.get("input_tokens", 0),
                    "completion_tokens": usage_raw.get("output_tokens", 0),
                    "total_tokens": usage_raw.get("input_tokens", 0) + usage_raw.get("output_tokens", 0)
                },
                "latency_ms": elapsed_ms,
                "raw": data
            }
