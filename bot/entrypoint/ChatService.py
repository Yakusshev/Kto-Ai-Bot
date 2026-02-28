import asyncio
import re

from aiogram.types import Message

from bot.domain.model.MessageForAiModel import MessageForAiModel
from bot.domain.model.SaveMessageModel import SaveMessageModel
from bot.domain.usecase.GenerateAiResponseUseCase import GenerateAiResponseUseCase, ROLE_USER, ROLE_ASSISTANT
from bot.domain.usecase.SaveMessageUseCase import SaveMessageUseCase
from bot.entrypoint.SaveMessageModelMapper import to_save_message_model
from bot.resource.Strings import Strings

GEMINI_CHAT_MODEL = 'gemini-pro'
GEMINI_SUMMARIZE_MODEL = 'gemini-1.5-flash'


class ChatService:

    def __init__(
        self,
        generate_ai_response_use_case: GenerateAiResponseUseCase,
        save_message_use_case: SaveMessageUseCase,
    ):
        self.save_message_use_case = save_message_use_case
        self.generate_ai_response_use_case = generate_ai_response_use_case
        self.system_prompt = None  # Оставляем None, будет инициализирован при первом вызове

    async def save_message_model(
        self,
        message: SaveMessageModel,
    ):
        await self.save_message_use_case.invoke(
            save_message_model_list = [message],
        )

    async def generate_ai_response(
        self,
        message_chat_id: int,
        user_name: str,
    ):
        ai_response = self.generate_ai_response_use_case.invoke(
            user_message_model = MessageForAiModel(
                id = message_chat_id,
                username = user_name,
            )
        )

        return await ai_response


    async def handle_self_message(
        self,
        message_list: list[Message],
        strings: Strings,
    ):
        save_message_model_list: list[SaveMessageModel] = []

        for message in message_list:
            save_message_model_list.append(
                to_save_message_model(
                    message = message,
                    content = message.text,
                    role = ROLE_ASSISTANT,
                    empty_message = strings.empty_message(),
                )
            )

        asyncio.create_task(
            self.save_message_use_case.invoke(
                save_message_model_list = save_message_model_list,
            )
        )


def truncate_ai_refusal(text: str) -> str:
    if not text:
        return ""
    refusal_patterns = [
        r"я не могу обсужд[а-я ]+ эту тему",
        r"я н могу обсуждать",
        r"давайте поговорим о чём-нибудь ещё",
        r"извините, но я не могу",
        r"как искусственный интеллект, я"
    ]
    combined_pattern = re.compile("|".join(refusal_patterns), re.IGNORECASE)
    match = combined_pattern.search(text)
    if match:
        cleaned_text = text[:match.start()].strip()
        return cleaned_text
    return text.strip()
