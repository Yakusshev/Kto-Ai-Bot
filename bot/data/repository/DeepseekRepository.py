from typing import List, Dict, Union, cast
from venv import logger

import openai
from openai.types.chat import ChatCompletionMessageParam

from bot.domain.repository.AiRepository import AiRepository

DEEPSEEK_CHAT_MODEL = 'deepseek-chat'
DEEPSEEK_SUMMARIZE_MODEL = 'deepseek-chat'


class DeepseekRepository(AiRepository):

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

        logger.info(f"DeepseekRepository.generate_response: requested")

        try:
            response = await self.async_client.chat.completions.create(
                model = self.model,
                messages = cast(List[ChatCompletionMessageParam], api_messages),
                stream = False,
            )
            response_text = response.choices[0].message.content

            self.log_history(api_messages, response_text)

            return response_text
        except Exception as e:
            print(
                f"Ошибка при обращении к OpenAI-совместимому API (model: url: {self.async_client.base_url}): {e}",
            )
            return "Ошибка обращения к AI"

    def log_history(self, api_messages, response_text):
        api_messages.append({"role": "assistant", "content": response_text})
        logger.info(f"DeepseekRepository.generate_response: response {api_messages}")
