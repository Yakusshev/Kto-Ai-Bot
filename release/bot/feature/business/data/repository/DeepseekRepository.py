from typing import List, cast
from venv import logger

import openai
from openai.types.chat import ChatCompletionMessageParam

from bot.feature.business.domain.model.MessageForAiModel import MessageForAiModel
from bot.feature.business.domain.repository.AiRepository import AiRepository

DEEPSEEK_CHAT_MODEL = 'deepseek-chat'
DEEPSEEK_SUMMARIZE_MODEL = 'deepseek-chat'

ROLE_TITLE = 'role'
ROLE_MODEL = 'model'
ROLE_SYSTEM = 'system'
CONTENT = 'content'


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
        message_list: List[MessageForAiModel],
        system_prompt: str,
    ) -> str:
        api_messages = []
        if system_prompt:
            api_messages.append(
                {
                    ROLE_TITLE: ROLE_SYSTEM,
                    CONTENT: system_prompt,
                },
            )

        for message in message_list:
            api_messages.append(
                {
                    ROLE_TITLE: message.role.value,
                    CONTENT: message.content,
                },
            )

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

    @staticmethod
    def log_history(
        api_messages,
        response_text,
    ):
        api_messages.append(
            {
                ROLE_TITLE: "assistant",
                CONTENT: response_text,
            },
        )
        logger.info(f"DeepseekRepository.generate_response: history = {api_messages}")
        logger.info(
            f"DeepseekRepository.generate_response: response {response_text}",
        )
