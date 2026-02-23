from typing import List, Dict, Union, cast

import openai
from openai.types.chat import ChatCompletionMessageParam

from bot.domain.repository.LLMRepository import LLMRepository

DEEPSEEK_CHAT_MODEL = 'deepseek-chat'
DEEPSEEK_SUMMARIZE_MODEL = 'deepseek-chat'

class DeepseekRepository(LLMRepository):
    def __init__(
        self,
        api_key: str,
        base_url: str,
    ):
        self.async_client = openai.AsyncOpenAI(
            api_key = api_key,
            base_url = base_url,
        )
        self.model = DEEPSEEK_CHAT_MODEL

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Union[str, None],
    ) -> str:
        api_messages = []
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})

        for msg in messages:
            api_messages.append({"role": msg["role"], "content": msg["content"]})

        try:
            response = await self.async_client.chat.completions.create(
                model = self.model,
                messages = cast(List[ChatCompletionMessageParam], api_messages),
                stream = False
            )
            return response.choices[0].message.content
        except Exception as e:
            print(
                f"Ошибка при обращении к OpenAI-совместимому API (model: {model}, url: {self.async_client.base_url}): {e}")
            return "Ошибка обращения к AI"
