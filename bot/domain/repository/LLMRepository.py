from abc import ABC, abstractmethod
from typing import Union, List, Dict

class LLMRepository(ABC):

    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Union[str, None]
    ) -> str:
        pass
