import os
import json
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from core.database import get_db_connection
from core.models import (
    LLMProviderModel,
    LLMModelInfo,
    LLMRoutingRuleModel,
    LLMUsageMetricModel,
    ModelGenerationRequest,
    ModelGenerationResponse
)
from core.adapters.base import ModelProvider
from core.adapters.mock_adapter import DeterministicMockProvider
from core.adapters.ollama_adapter import OllamaProvider
from core.adapters.cloud_adapters import OpenAICompatibleProvider, GeminiProvider, AnthropicProvider
from core.security.vault import VaultProvider

logger = logging.getLogger("ai_workforce_os.model_manager")

class ModelManager:
    """
    Central, provider-independent LLM Management & Routing Engine for AI Workforce OS.
    
    Responsibilities:
    1. Provider & Model Lifecycle (Ollama, OpenAI, Gemini, Anthropic, Mock).
    2. Dynamic Task-Based Routing & Local-Only Boundary Enforcement.
    3. Health Monitoring, Latency Tracking, and Usage Auditing.
    4. Secure Credential Resolution via Fernet AES-128 Vault.
    5. Fallback Policy Execution with Zero Silent Cloud Leaks.
    """
    _instance: Optional["ModelManager"] = None

    def __init__(self):
        self.vault = VaultProvider()
        self._provider_cache: Dict[str, ModelProvider] = {}
        # Always register the deterministic mock provider as baseline offline fallback
        self._provider_cache["mock:mock-deterministic-v1"] = DeterministicMockProvider("mock-deterministic-v1")

    @classmethod
    def get_instance(cls) -> "ModelManager":
        if cls._instance is None:
            cls._instance = ModelManager()
        return cls._instance

    async def initialize_defaults(self):
        """Populate default providers, models, and routing rules in the database if empty."""
        async with get_db_connection() as db:
            # 1. Check if providers exist
            async with db.execute("SELECT COUNT(*) as cnt FROM llm_providers") as cursor:
                row = await cursor.fetchone()
                provider_count = row["cnt"] if row else 0

            if provider_count == 0:
                logger.info("Initializing baseline LLM providers and models...")
                # Register Default Providers
                providers = [
                    ("mock_provider", "Deterministic Offline Engine", "mock", "offline://localhost", None, 1, "healthy"),
                    ("ollama_local", "Local Ollama Inference", "local_ollama", "http://localhost:11434", None, 1, "unknown"),
                    ("openai_cloud", "OpenAI Cloud API", "cloud_openai", "https://api.openai.com/v1", None, 1, "unauthenticated"),
                    ("gemini_cloud", "Google Gemini API", "cloud_gemini", "https://generativelanguage.googleapis.com", None, 1, "unauthenticated"),
                    ("anthropic_cloud", "Anthropic Claude API", "cloud_anthropic", "https://api.anthropic.com", None, 1, "unauthenticated")
                ]
                for p in providers:
                    await db.execute(
                        """
                        INSERT INTO llm_providers (id, name, provider_type, base_url, api_key_ref, is_active, health_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        p
                    )

                # Register Baseline Models
                models = [
                    # id, provider_id, model_name, display_name, classification, context_window, supports_tools, supports_structured, vision, caps, is_active, is_default
                    ("mock-default", "mock_provider", "mock-deterministic-v1", "Deterministic Local Mock", "mock", 8192, 1, 1, 0, json.dumps(["general", "fast", "testing"]), 1, 1),
                    ("ollama-llama32", "ollama_local", "llama3.2:latest", "Llama 3.2 3B (Local)", "local", 8192, 1, 1, 0, json.dumps(["general", "coding", "fast", "local_only"]), 1, 0),
                    ("ollama-qwen25", "ollama_local", "qwen2.5-coder:7b", "Qwen 2.5 Coder 7B (Local)", "local", 16384, 1, 1, 0, json.dumps(["coding", "reasoning", "local_only"]), 1, 0),
                    ("openai-gpt4o-mini", "openai_cloud", "gpt-4o-mini", "GPT-4o Mini (Cloud)", "cloud", 128000, 1, 1, 1, json.dumps(["general", "fast", "coding"]), 1, 0),
                    ("openai-gpt4o", "openai_cloud", "gpt-4o", "GPT-4o (Cloud)", "cloud", 128000, 1, 1, 1, json.dumps(["reasoning", "coding", "general"]), 1, 0),
                    ("gemini-15-flash", "gemini_cloud", "gemini-1.5-flash", "Gemini 1.5 Flash (Cloud)", "cloud", 1000000, 1, 1, 1, json.dumps(["general", "fast", "research"]), 1, 0),
                    ("gemini-15-pro", "gemini_cloud", "gemini-1.5-pro", "Gemini 1.5 Pro (Cloud)", "cloud", 2000000, 1, 1, 1, json.dumps(["reasoning", "coding", "deep_research"]), 1, 0),
                    ("claude-35-sonnet", "anthropic_cloud", "claude-3-5-sonnet-20241022", "Claude 3.5 Sonnet (Cloud)", "cloud", 200000, 1, 1, 1, json.dumps(["coding", "reasoning", "architecture"]), 1, 0)
                ]
                for m in models:
                    await db.execute(
                        """
                        INSERT INTO llm_models (id, provider_id, model_name, display_name, classification, context_window, supports_tools, supports_structured_output, supports_vision, capabilities, is_active, is_default)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        m
                    )

                # Register Baseline Routing Rules
                routing_rules = [
                    # id, rule_name, task_category, agent_id_match, privacy_level, preferred_model_id, fallback_model_id, allow_cloud_fallback, priority
                    ("rule_sensitive_local", "Sensitive / Local Operations", "*", "*", "local_only", "ollama-llama32", "mock-default", 0, 100),
                    ("rule_coding_complex", "Complex Software Engineering", "code", "software-engineer", "standard", "claude-35-sonnet", "mock-default", 1, 80),
                    ("rule_research_market", "Deep Market & SEO Research", "research", "market-seo-geo-researcher", "standard", "gemini-15-flash", "mock-default", 1, 70),
                    ("rule_default_fallback", "Default System Routing", "*", "*", "standard", "mock-default", "mock-default", 0, 10)
                ]
                for r in routing_rules:
                    await db.execute(
                        """
                        INSERT INTO llm_routing_rules (id, rule_name, task_category, agent_id_match, privacy_level, preferred_model_id, fallback_model_id, allow_cloud_fallback, priority)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        r
                    )
                await db.commit()
                logger.info("Initialized default LLM providers, models, and routing rules.")

    async def list_providers(self) -> List[Dict[str, Any]]:
        """List all configured LLM providers with current health status."""
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM llm_providers ORDER BY created_at ASC") as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def list_models(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """List registered models with capability metadata and provider details."""
        async with get_db_connection() as db:
            query = """
                SELECT m.*, p.name as provider_name, p.provider_type, p.base_url, p.health_status as provider_health
                FROM llm_models m
                JOIN llm_providers p ON m.provider_id = p.id
            """
            if active_only:
                query += " WHERE m.is_active = 1 AND p.is_active = 1"
            query += " ORDER BY m.is_default DESC, m.created_at ASC"
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                results = []
                for r in rows:
                    item = dict(r)
                    if isinstance(item.get("capabilities"), str):
                        try:
                            item["capabilities"] = json.loads(item["capabilities"])
                        except Exception:
                            item["capabilities"] = []
                    results.append(item)
                return results

    async def get_system_reasoning_status(self) -> Dict[str, Any]:
        """
        Conducts an honest audit of current reasoning capabilities:
        Reports whether the OS is using a real LLM or an offline mock,
        and identifies active providers and credentials.
        """
        async with get_db_connection() as db:
            # Check default model
            async with db.execute("SELECT m.*, p.provider_type, p.health_status, p.base_url FROM llm_models m JOIN llm_providers p ON m.provider_id = p.id WHERE m.is_default = 1") as cursor:
                default_row = await cursor.fetchone()
                default_model = dict(default_row) if default_row else None

            # Check healthy providers
            async with db.execute("SELECT * FROM llm_providers WHERE health_status = 'healthy'") as cursor:
                healthy_providers = [dict(r) for r in await cursor.fetchall()]

        # Check environment and local Ollama reachability
        ollama_status = await OllamaProvider().check_health()

        is_mock = default_model is None or default_model.get("provider_type") == "mock"
        status_label = "MOCKED_OR_SIMULATED" if is_mock else "ACTIVE_LLM_CONFIGURED"

        return {
            "status": status_label,
            "is_real_llm_active": not is_mock and default_model.get("health_status") == "healthy",
            "active_model": default_model["model_name"] if default_model else "mock-deterministic-v1",
            "active_provider": default_model["provider_type"] if default_model else "mock",
            "classification": default_model["classification"] if default_model else "mock",
            "ollama_local_detected": ollama_status.get("available", False),
            "ollama_models": ollama_status.get("models", []),
            "healthy_providers_count": len(healthy_providers),
            "notice": (
                "The OS is currently operating on the offline deterministic reasoning engine (simulation). "
                "No live external API tokens or local Ollama daemon were found active. "
                "To enable live reasoning, install Ollama locally or configure an API key via the Model Manager dashboard."
                if is_mock else "Live reasoning provider is configured and active."
            )
        }

    async def set_default_model(self, model_id: str) -> Dict[str, Any]:
        """Set a registered model as the default model."""
        async with get_db_connection() as db:
            await db.execute("UPDATE llm_models SET is_default = 0")
            result = await db.execute("UPDATE llm_models SET is_default = 1 WHERE id = ?", (model_id,))
            if result.rowcount == 0:
                raise ValueError(f"Model ID '{model_id}' not found.")
            await db.commit()
            return {"status": "success", "default_model_id": model_id}

    async def update_provider_credential(self, provider_id: str, api_key: str) -> Dict[str, Any]:
        """Securely encrypt and store a provider API key in the Vault."""
        if not api_key:
            raise ValueError("API key cannot be empty.")
        encrypted = self.vault.encrypt(api_key.strip())
        async with get_db_connection() as db:
            # Store encrypted key reference in config_json
            config = {"encrypted_api_key": encrypted}
            await db.execute(
                "UPDATE llm_providers SET config_json = ?, health_status = 'unknown' WHERE id = ?",
                (json.dumps(config), provider_id)
            )
            await db.commit()
            # Invalidate any cached adapter
            self._provider_cache = {k: v for k, v in self._provider_cache.items() if not k.startswith(provider_id)}
            return {"status": "success", "provider_id": provider_id, "message": "API key encrypted and stored securely."}

    async def check_provider_health(self, provider_id: str) -> Dict[str, Any]:
        """Test reachability and authentication for a specific provider."""
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM llm_providers WHERE id = ?", (provider_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return {"status": "error", "message": f"Provider '{provider_id}' not found."}
                provider = dict(row)

        provider_type = provider.get("provider_type")
        config = json.loads(provider.get("config_json") or "{}")
        raw_key = ""
        if "encrypted_api_key" in config:
            try:
                raw_key = self.vault.decrypt(config["encrypted_api_key"])
            except Exception as e:
                logger.error(f"Failed to decrypt key for {provider_id}: {e}")

        health_result: Dict[str, Any] = {"status": "unknown"}
        if provider_type == "mock":
            health_result = {"status": "healthy", "available": True, "message": "Offline deterministic provider always ready."}
        elif provider_type == "local_ollama":
            adapter = OllamaProvider(base_url=provider.get("base_url", "http://localhost:11434"))
            health_result = await adapter.check_health()
        elif provider_type == "cloud_openai":
            adapter = OpenAICompatibleProvider(base_url=provider.get("base_url", "https://api.openai.com/v1"), api_key=raw_key)
            health_result = await adapter.check_health()
        elif provider_type == "cloud_gemini":
            adapter = GeminiProvider(api_key=raw_key)
            health_result = await adapter.check_health()
        elif provider_type == "cloud_anthropic":
            adapter = AnthropicProvider(api_key=raw_key)
            health_result = await adapter.check_health()

        # Update provider health in DB
        async with get_db_connection() as db:
            status_str = health_result.get("status", "unknown")
            await db.execute(
                "UPDATE llm_providers SET health_status = ?, last_health_check = CURRENT_TIMESTAMP WHERE id = ?",
                (status_str, provider_id)
            )
            await db.commit()

        return health_result

    async def _resolve_adapter(self, provider_row: Dict[str, Any], model_name: str) -> ModelProvider:
        """Instantiate or retrieve cached adapter with decrypted credentials."""
        cache_key = f"{provider_row['id']}:{model_name}"
        if cache_key in self._provider_cache:
            return self._provider_cache[cache_key]

        ptype = provider_row.get("provider_type")
        base_url = provider_row.get("base_url")
        config = json.loads(provider_row.get("config_json") or "{}")
        api_key = ""
        if "encrypted_api_key" in config:
            try:
                api_key = self.vault.decrypt(config["encrypted_api_key"])
            except Exception as e:
                logger.warning(f"Failed to decrypt key for {provider_row['id']}: {e}")

        # Check environment fallback
        if not api_key:
            if ptype == "cloud_openai":
                api_key = os.getenv("OPENAI_API_KEY", "")
            elif ptype == "cloud_gemini":
                api_key = os.getenv("GEMINI_API_KEY", "")
            elif ptype == "cloud_anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY", "")

        adapter: ModelProvider
        if ptype == "mock":
            adapter = DeterministicMockProvider(model_name)
        elif ptype == "local_ollama":
            adapter = OllamaProvider(base_url=base_url or "http://localhost:11434", model_name=model_name)
        elif ptype == "cloud_openai":
            adapter = OpenAICompatibleProvider(base_url=base_url or "https://api.openai.com/v1", api_key=api_key, model_name=model_name)
        elif ptype == "cloud_gemini":
            adapter = GeminiProvider(api_key=api_key, model_name=model_name)
        elif ptype == "cloud_anthropic":
            adapter = AnthropicProvider(api_key=api_key, model_name=model_name)
        else:
            adapter = DeterministicMockProvider(model_name)

        self._provider_cache[cache_key] = adapter
        return adapter

    async def route_model(self, request: ModelGenerationRequest) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Dynamically select the optimal model and provider based on routing rules and privacy boundary.
        Enforces strict zero-silent-cloud-leakage policy.
        """
        async with get_db_connection() as db:
            # 1. Check if model is forced
            if request.force_model_id:
                async with db.execute(
                    "SELECT m.*, p.provider_type, p.base_url, p.config_json, p.health_status FROM llm_models m JOIN llm_providers p ON m.provider_id = p.id WHERE m.id = ?",
                    (request.force_model_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        model_data = dict(row)
                        # Check privacy violation
                        if request.privacy_level in ("local_only", "sensitive") and model_data["classification"] == "cloud":
                            raise PermissionError(
                                f"Privacy Violation: Task requires '{request.privacy_level}' execution, but forced model '{request.force_model_id}' is a CLOUD model."
                            )
                        return model_data, model_data

            # 2. Check routing rules
            async with db.execute(
                """
                SELECT r.*, m.id as model_id, m.model_name, m.classification, m.is_active as model_active,
                       p.id as provider_id, p.provider_type, p.base_url, p.config_json, p.health_status,
                       fm.id as fb_model_id, fm.model_name as fb_model_name, fm.classification as fb_classification,
                       fp.id as fb_provider_id, fp.provider_type as fb_provider_type, fp.base_url as fb_base_url, fp.config_json as fb_config_json, fp.health_status as fb_health_status
                FROM llm_routing_rules r
                JOIN llm_models m ON r.preferred_model_id = m.id
                JOIN llm_providers p ON m.provider_id = p.id
                LEFT JOIN llm_models fm ON r.fallback_model_id = fm.id
                LEFT JOIN llm_providers fp ON fm.provider_id = fp.id
                WHERE r.is_active = 1
                ORDER BY r.priority DESC
                """
            ) as cursor:
                rules = await cursor.fetchall()
                for rule in rules:
                    # Match task_category
                    if rule["task_category"] != "*" and rule["task_category"] != request.task_type:
                        continue
                    # Match agent_id
                    if rule["agent_id_match"] != "*" and request.agent_id and rule["agent_id_match"] != request.agent_id:
                        continue
                    # Match privacy level
                    if rule["privacy_level"] == "local_only" and request.privacy_level not in ("local_only", "sensitive"):
                        continue

                    # Selected rule candidate
                    is_cloud = rule["classification"] == "cloud"
                    if request.privacy_level in ("local_only", "sensitive") and is_cloud:
                        # Cannot use cloud for local-only
                        continue

                    # If provider is healthy or mock
                    if rule["health_status"] == "healthy" or rule["provider_type"] == "mock":
                        model_dict = {
                            "id": rule["model_id"],
                            "model_name": rule["model_name"],
                            "classification": rule["classification"],
                            "provider_id": rule["provider_id"],
                            "provider_type": rule["provider_type"],
                            "base_url": rule["base_url"],
                            "config_json": rule["config_json"],
                            "health_status": rule["health_status"]
                        }
                        return model_dict, rule

            # 3. Fallback to default active model
            async with db.execute(
                """
                SELECT m.*, p.provider_type, p.base_url, p.config_json, p.health_status
                FROM llm_models m
                JOIN llm_providers p ON m.provider_id = p.id
                WHERE m.is_default = 1 AND m.is_active = 1
                """
            ) as cursor:
                def_row = await cursor.fetchone()
                if def_row:
                    model_dict = dict(def_row)
                    if request.privacy_level in ("local_only", "sensitive") and model_dict["classification"] == "cloud":
                        # Must fall back to offline mock rather than leaking to cloud
                        logger.warning("Default model is cloud but request is local_only; falling back to offline mock.")
                        return await self._get_mock_model_dict(db)
                    return model_dict, model_dict

            # 4. Ultimate fallback: offline mock
            return await self._get_mock_model_dict(db)

    async def _get_mock_model_dict(self, db) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        async with db.execute(
            """
            SELECT m.*, p.provider_type, p.base_url, p.config_json, p.health_status
            FROM llm_models m
            JOIN llm_providers p ON m.provider_id = p.id
            WHERE m.id = 'mock-default'
            """
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                d = dict(row)
                return d, d
            # Hardcoded dictionary if db row missing
            fallback = {
                "id": "mock-default",
                "model_name": "mock-deterministic-v1",
                "classification": "mock",
                "provider_id": "mock_provider",
                "provider_type": "mock",
                "base_url": "offline://localhost",
                "config_json": "{}",
                "health_status": "healthy"
            }
            return fallback, fallback

    async def generate(self, request: ModelGenerationRequest) -> ModelGenerationResponse:
        """
        Execute generation across dynamically selected provider with fallback and metric logging.
        """
        start_time = time.perf_counter()
        selected_model, rule = await self.route_model(request)

        # Attempt invocation
        try:
            adapter = await self._resolve_adapter(selected_model, selected_model["model_name"])
            resp = await adapter.generate(
                system_prompt=request.system_prompt,
                user_prompt=request.user_prompt,
                context=request.context,
                tools=request.tools
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            # Parse JSON if possible
            parsed_json = resp.get("parsed_json")
            if parsed_json is None and resp.get("content"):
                try:
                    parsed_json = json.loads(resp["content"])
                except Exception:
                    pass

            response = ModelGenerationResponse(
                content=resp["content"],
                parsed_json=parsed_json,
                provider=resp["provider"],
                model=resp["model"],
                classification=resp.get("classification", selected_model["classification"]),
                usage=resp.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}),
                latency_ms=elapsed_ms,
                raw=resp.get("raw")
            )

            # Log metrics
            await self._record_metric(
                task_id=request.context.get("task_id"),
                step_id=request.context.get("step_id"),
                agent_id=request.agent_id,
                model_id=selected_model["id"],
                provider_id=selected_model["provider_id"],
                prompt_tokens=response.usage["prompt_tokens"],
                completion_tokens=response.usage["completion_tokens"],
                latency_ms=elapsed_ms,
                success=True
            )
            return response

        except Exception as e:
            logger.error(f"Generation failed on preferred model {selected_model['model_name']}: {e}")
            # Check if fallback is permitted
            allow_fallback = rule.get("allow_cloud_fallback", 0) if isinstance(rule, dict) else 0
            if request.privacy_level in ("local_only", "sensitive"):
                allow_fallback = 0 # Strictly forbid cloud fallback for local-only

            if selected_model["provider_type"] != "mock":
                logger.info(f"Attempting fallback to offline deterministic engine for resilience...")
                async with get_db_connection() as db:
                    mock_model, _ = await self._get_mock_model_dict(db)
                mock_adapter = await self._resolve_adapter(mock_model, mock_model["model_name"])
                resp = await mock_adapter.generate(
                    system_prompt=request.system_prompt,
                    user_prompt=request.user_prompt,
                    context=request.context,
                    tools=request.tools
                )
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                await self._record_metric(
                    task_id=request.context.get("task_id"),
                    step_id=request.context.get("step_id"),
                    agent_id=request.agent_id,
                    model_id="mock-default",
                    provider_id="mock_provider",
                    prompt_tokens=resp.get("usage", {}).get("prompt_tokens", 0),
                    completion_tokens=resp.get("usage", {}).get("completion_tokens", 0),
                    latency_ms=elapsed_ms,
                    success=True,
                    error_message=f"Primary model {selected_model['id']} failed: {str(e)}"
                )
                return ModelGenerationResponse(
                    content=resp["content"],
                    parsed_json=resp.get("parsed_json"),
                    provider="mock_provider_fallback",
                    model=mock_model["model_name"],
                    classification="mock",
                    usage=resp.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}),
                    latency_ms=elapsed_ms,
                    raw={"fallback_from": selected_model["id"], "error": str(e)}
                )
            raise

    async def _record_metric(
        self,
        task_id: Optional[str],
        step_id: Optional[str],
        agent_id: Optional[str],
        model_id: str,
        provider_id: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        success: bool,
        error_message: Optional[str] = None
    ):
        try:
            async with get_db_connection() as db:
                await db.execute(
                    """
                    INSERT INTO llm_usage_metrics
                    (task_id, step_id, agent_id, model_id, provider_id, prompt_tokens, completion_tokens, latency_ms, success, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (task_id, step_id, agent_id, model_id, provider_id, prompt_tokens, completion_tokens, latency_ms, 1 if success else 0, error_message)
                )
                await db.commit()
        except Exception as err:
            logger.warning(f"Failed to record LLM metric: {err}")
