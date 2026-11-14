from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class ModelProvider(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str, context: Dict[str, Any], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Generate model response or tool decision."""
        pass

class RuntimeAdapter(ABC):
    @abstractmethod
    async def execute(self, action: str, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute action via this runtime adapter."""
        pass
