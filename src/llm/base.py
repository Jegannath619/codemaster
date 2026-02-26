from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any

class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    """

    @abstractmethod
    async def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Generates a response from the LLM.

        Args:
            system_prompt: The system prompt to set context.
            user_prompt: The user's input.
            tools: Optional list of tools (functions) available to the LLM.

        Returns:
            The generated text response.
        """
        pass
