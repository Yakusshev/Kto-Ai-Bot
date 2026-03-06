import asyncio
import logging
import re

from aiogram.types import Message

from bot.feature.business.domain.model.SaveMessageModel import SaveMessageModel, \
    MessageRole
from bot.feature.business.domain.model.UserMessageInfoForAiModel import \
    UserMessageInfoForAiModel
from bot.feature.business.domain.scenario.GenerateAiReponseScenario import \
    GenerateAiResponseScenario
from bot.feature.business.domain.usecase.SaveMessageUseCase import SaveMessageUseCase
from bot.feature.business.entrypoint.SaveMessageModelMapper import \
    to_save_message_model
from bot.resource.Strings import Strings

_logger = logging.getLogger("ChatService")

class ChatService:

    def __init__(
        self,
        generate_ai_response_scenario: GenerateAiResponseScenario,
        save_message_use_case: SaveMessageUseCase,
        strings: Strings,
    ):
        self.save_message_use_case = save_message_use_case
        self.generate_ai_response_scenario = generate_ai_response_scenario
        self.strings = strings

    async def save_message(
        self,
        message: Message,
        text_content: str,
        role: MessageRole,
    ):
        save_message_model = to_save_message_model(
            message = message,
            content = text_content,
            role = role,
            empty_message = self.strings.empty_message(),
        )

        await self.save_message_use_case.invoke(
            save_message_model_list = [save_message_model],
        )

    async def generate_ai_response(
        self,
        message: Message,
    ):
        ai_response = self.generate_ai_response_scenario.invoke(
            user_for_ai_model = UserMessageInfoForAiModel(
                id = message.chat.id,
                username = message.from_user.username,
                full_name = message.from_user.full_name,
                datetime = message.date,
            ),
        )

        return await ai_response

    async def save_assistant_text_message_list(
        self,
        message_list: list[Message],
    ):
        save_message_model_list: list[SaveMessageModel] = []

        for message in message_list:
            save_message_model_list.append(
                to_save_message_model(
                    message = message,
                    content = message.text,
                    role = MessageRole.ASSISTANT,
                    empty_message = self.strings.empty_message(),
                ),
            )

        asyncio.create_task(
            self.save_message_use_case.invoke(
                save_message_model_list = save_message_model_list,
            ),
        )


def truncate_ai_refusal(text: str) -> str:
    if not text:
        return ""
    refusal_patterns = [
        r"я не могу обсужд[а-я ]+ эту тему",
        r"я н могу обсуждать",
        r"давайте поговорим о чём-нибудь ещё",
        r"извините, но я не могу",
        r"как искусственный интеллект, я",
    ]
    combined_pattern = re.compile("|".join(refusal_patterns), re.IGNORECASE)
    match = combined_pattern.search(text)
    if match:
        cleaned_text = text[:match.start()].strip()
        return cleaned_text
    return text.strip()
