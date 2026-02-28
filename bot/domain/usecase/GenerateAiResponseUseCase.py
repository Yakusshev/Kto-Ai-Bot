import re
from random import random
from typing import List
from venv import logger

from bot.data.repository.ChatHistoryRepositoryImpl import ChatHistoryRepositoryImpl
from bot.domain.DefaultSystemInstuction import anya_system_instruction
from bot.domain.model.MessageForAiModel import MessageForAiModel
from bot.domain.model.SaveMessageModel import SaveMessageModel, MessageRole
from bot.domain.model.UserInfoForAiModel import UserInfoForAiModel
from bot.domain.repository.AiRepository import AiRepository


class GenerateAiResponseUseCase:
    NEXT_MESSAGE_TAG = '[next]'
    NEXT_MESSAGE_TAG_REGEX = r'\[next\]'
    DATE_FORMAT = "%d.%m"
    TIME_FORMAT = "%H:%M"

    def __init__(
        self,
        ai_repository: AiRepository,
        session_repository: ChatHistoryRepositoryImpl,
    ):
        self.llm_repository = ai_repository
        self.session_repository = session_repository

    async def invoke(
        self,
        user_message_model: UserInfoForAiModel,
    ) -> List[str]:

        history: List[SaveMessageModel] = await self.session_repository \
            .get_session_data(chat_id = user_message_model.id)

        ai_list: List[MessageForAiModel] = []

        for index, message in enumerate(history):

            date_time = await self.get_date_time(
                previous_message = history[index - 1] if index != 0 else None,
                message = message,
            )
            if ai_list and ai_list[-1].role == message.role:

                previous_ai_message = ai_list[-1]

                ai_list[-1] = MessageForAiModel(
                    role = message.role,
                    content = f'{previous_ai_message.content}'
                              f'{GenerateAiResponseUseCase.NEXT_MESSAGE_TAG}'
                              f'{date_time}{message.content}',
                )
            else:
                ai_list.append(
                    MessageForAiModel(
                        role = message.role,
                        content = f'{date_time}{message.content}',
                    ),
                )

        ai_response = await self.llm_repository.generate_response(
            message_list = ai_list,
            system_prompt = anya_system_instruction(
                user_nickname = user_message_model.username,
                next_message_tag = GenerateAiResponseUseCase.NEXT_MESSAGE_TAG,
            ),
        )

        return self.split_messages(response = ai_response)

    @staticmethod
    async def get_date_time(
        previous_message: SaveMessageModel | None,
        message: SaveMessageModel,
    ) -> str:

        if message.role == MessageRole.ASSISTANT:
            return ''

        date_time = ''

        date = message.created_at \
            .strftime(format = GenerateAiResponseUseCase.DATE_FORMAT)
        time = message.created_at \
            .strftime(format = GenerateAiResponseUseCase.TIME_FORMAT)

        if previous_message is None:
            date_time = f'[{date} {time}]'
        else:
            prev_date = previous_message \
                .created_at \
                .strftime(format = GenerateAiResponseUseCase.DATE_FORMAT)
            prev_time = previous_message \
                .created_at \
                .strftime(format = GenerateAiResponseUseCase.TIME_FORMAT)

            if prev_date != date:
                date_time += f'{date}'
            if prev_time != time:
                date_time = f'{date_time} {time}'

            if date_time:
                date_time = f'[{date_time}]'

        return date_time

    @staticmethod
    def split_messages(
        response: str,
    ) -> List[str]:

        lines = GenerateAiResponseUseCase.replace_brackets_except_next(response)\
            .split(fr'\n|\n\n|{GenerateAiResponseUseCase.NEXT_MESSAGE_TAG_REGEX}')

        if not lines:
            logger.warning(
                f'GenerateAiResponseUseCase.split_messages: empty lines; '
                f'response = {response}',
            )
            return []

        result = []
        current = lines[0]

        for line in lines[1:]:
            if random() < 0.3:
                result.append(current)
                current = line
            else:
                current += '\n' + line

        result.append(current)

        return result

    @staticmethod
    def replace_brackets_except_next(text: str) -> str:
        """
        Заменяет все вхождения вида [что-то] на пробел,
        за исключением точного тега [next], который сохраняется.
        """
        # Шаблон: открывающая скобка, затем любое количество символов, не содержащих ']',
        # затем закрывающая скобка. Это покрывает большинство простых случаев без вложенности.
        pattern = r'\[[^\]]*\]'

        def replacer(match):
            token = match.group(0)
            # Если это точно тег [next], оставляем как есть
            if token == '[next]':
                return token
            # Иначе заменяем на пробел
            return ' '

        return re.sub(pattern, replacer, text)
