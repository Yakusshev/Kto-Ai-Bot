from abc import ABC, abstractmethod
from typing import List

from bot.feature.business.domain.model.MessageForAiModel import MessageForAiModel


class AiRepository(ABC):

    @abstractmethod
    async def generate_response(
        self,
        message_list: List[MessageForAiModel],
        system_prompt: str,
    ) -> str:
        pass
