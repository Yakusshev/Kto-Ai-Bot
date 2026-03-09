import asyncio
import logging
import re

from aiogram.types import Message, BusinessConnection

from bot.feature.business.domain.model.SaveMessageModel import SaveMessageModel, \
    MessageRole, OwnerModel
from bot.feature.business.domain.model.UserMessageInfoForAiModel import \
    UserMessageInfoForAiModel
from bot.feature.business.domain.scenario.GenerateAiReponseScenario import \
    GenerateAiResponseScenario
from bot.feature.business.domain.usecase.SaveMessageUseCase import SaveMessageUseCase
from bot.feature.business.entrypoint.SaveMessageModelMapper import \
    to_save_message_model
from bot.resource.Strings import Strings
from bot.util.log_util import get_logger


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
        )

        if save_message_model:
            await self.save_message_use_case.invoke(
                save_message_model_list = [save_message_model],
            )
        else:
            _logger.warning(
                f"save_message: пустой text_content, "
                f"role = {role}, message = {message}",
            )

    async def generate_ai_response(
        self,
        message: Message,
        business_connection: BusinessConnection,
    ):
        ai_response = self.generate_ai_response_scenario.invoke(
            user_for_ai_model = UserMessageInfoForAiModel(
                chat_id = message.chat.id,
                username = message.from_user.username,
                full_name = message.from_user.full_name,
                datetime = message.date,
            ),
            owner_model = OwnerModel(
                id = business_connection.user.id,
                username = business_connection.user.username,
                full_name = business_connection.user.full_name,
            ),
        )

        return await ai_response

    async def save_assistant_text_message_list(
        self,
        message_list: list[Message],
    ):
        save_message_model_list: list[SaveMessageModel] = []

        for message in message_list:
            save_message_model = to_save_message_model(
                message = message,
                content = message.text,
                role = MessageRole.ASSISTANT,
            )

            if save_message_model:
                save_message_model_list.append(save_message_model)
            else:
                _logger.warning(
                    f"save_message: пустой text_content, message = {message}",
                )

        await self.save_message_use_case.invoke(
            save_message_model_list = save_message_model_list,
        ),

_logger = get_logger(ChatService.__name__)