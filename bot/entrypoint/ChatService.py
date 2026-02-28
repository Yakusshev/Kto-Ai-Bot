import asyncio
import re

from aiogram.types import Message

from bot.domain.model.UserInfoForAiModel import UserInfoForAiModel
from bot.domain.model.SaveMessageModel import SaveMessageModel
from bot.domain.usecase.GenerateAiResponseUseCase import GenerateAiResponseUseCase
from bot.domain.usecase.SaveMessageUseCase import SaveMessageUseCase
from bot.entrypoint.SaveMessageModelMapper import to_save_message_model
from bot.resource.Strings import Strings

ROLE_ASSISTANT = 'assistant'
ROLE_USER = 'user'

class ChatService:

    def __init__(
        self,
        generate_ai_response_use_case: GenerateAiResponseUseCase,
        save_message_use_case: SaveMessageUseCase,
        strings: Strings,
    ):
        self.save_message_use_case = save_message_use_case
        self.generate_ai_response_use_case = generate_ai_response_use_case
        self.strings = strings  # Оставляем None, будет инициализирован при первом вызове

    async def save_message_model(
        self,
        message: Message,
        text_content: str,
    ):
        save_message_model = to_save_message_model(
            message = message,
            content = text_content,
            role = ROLE_USER,
            empty_message = self.strings.empty_message(),
        )

        await self.save_message_use_case.invoke(
            save_message_model_list = [save_message_model],
        )

    async def generate_ai_response(
        self,
        message_chat_id: int,
        user_name: str,
    ):
        ai_response = self.generate_ai_response_use_case.invoke(
            user_message_model = UserInfoForAiModel(
                id = message_chat_id,
                username = user_name,
            ),
        )

        return await ai_response

    async def handle_self_message(
        self,
        message_list: list[Message],
    ):
        save_message_model_list: list[SaveMessageModel] = []

        for message in message_list:
            save_message_model_list.append(
                to_save_message_model(
                    message = message,
                    content = message.text,
                    role = ROLE_ASSISTANT,
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
