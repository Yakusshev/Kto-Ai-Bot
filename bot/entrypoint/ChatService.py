import asyncio
import re

from aiogram.types import Message

from bot.domain.model.SaveMessageModel import SaveMessageModel
from bot.domain.model.UserMessageModel import UserMessageModel
from bot.domain.usecase.GenerateAiResponseUseCase import GenerateAiResponseUseCase, ROLE_USER, ROLE_ASSISTANT
from bot.domain.usecase.SaveMessageUseCase import SaveMessageUseCase
from bot.entrypoint.SaveMessageModelMapper import to_save_message_model

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

    async def handle_user_text_message(
        self,
        message: Message,
        content: str,
    ) -> list[str]:

        ai_response = await self.generate_ai_response_use_case.invoke(
            user_message_model = UserMessageModel(
                id = message.chat.id,
                username = message.chat.username,
                content = content,
            )
        )

        asyncio.create_task(
            self.save_message_use_case.invoke(
                save_message_model = to_save_message_model(
                    message = message,
                    content = content,
                    role = ROLE_USER,
                )
            )
        )

        return truncate_ai_refusal(ai_response).split('\n')

    async def handle_self_message(
        self,
        message: Message,
    ):
        asyncio.create_task(
            self.save_message_use_case.invoke(
                save_message_model = to_save_message_model(
                    message = message,
                    content = message.text,
                    role = ROLE_ASSISTANT,
                )
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
