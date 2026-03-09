import logging
from typing import List, cast

import openai
from openai.types.chat import ChatCompletionMessageParam

from bot.feature.business.domain.model.MessageForAiModel import MessageForAiModel
from bot.feature.business.domain.repository.AiRepository import AiRepository
from bot.util.log_util import get_logger

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
            logger.error(
                f"Ошибка при обращении к OpenAI-совместимому API (model: "
                f"url: {self.async_client.base_url}): {e}",
            )
            raise e

    @staticmethod
    def log_history(
        api_messages,
        response_text,
    ):
        length = len(api_messages)
        request = api_messages[length - 1]

        logger.info(
            f'''generate_response:
                request: {request}
                response: {response_text}
            ''',
        )

        api_messages.append(
            {
                ROLE_TITLE: "assistant",
                CONTENT: response_text,
            },
        )
        logger.debug(f"generate_response: history = {api_messages}")


logger = get_logger(DeepseekRepository.__name__)
