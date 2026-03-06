import re
from random import random
from typing import List
from venv import logger

from bot.feature.business.data.repository.ChatHistoryRepositoryImpl import ChatHistoryRepositoryImpl
from bot.feature.business.domain.model.MessageForAiModel import MessageForAiModel
from bot.feature.business.domain.model.SaveMessageModel import SaveMessageModel, MessageRole
from bot.feature.business.domain.model.UserMessageInfoForAiModel import UserMessageInfoForAiModel
from bot.feature.business.domain.repository.AiRepository import AiRepository
from bot.feature.business.domain.usecase.GetSystemInstructionUseCase import \
    GetSystemInstructionUseCase


class GenerateAiResponseUseCase:
    NEXT_MESSAGE_TAG = '[next]'
    NEXT_MESSAGE_TAG_REGEX = r'\[next\]'
    DATE_FORMAT = "%d.%m"
    TIME_FORMAT = "%H:%M"

    def __init__(
        self,
        ai_repository: AiRepository,
        session_repository: ChatHistoryRepositoryImpl,
        get_system_instruction_use_case: GetSystemInstructionUseCase,
    ):
        self.llm_repository = ai_repository
        self.session_repository = session_repository
        self.get_system_instruction_use_case = get_system_instruction_use_case

    async def invoke(
        self,
        user_for_ai_model: UserMessageInfoForAiModel,
    ) -> List[str]:

        history: List[SaveMessageModel] = await self.session_repository \
            .get_session_data(chat_id = user_for_ai_model.id)

        ai_list: List[MessageForAiModel] = []

        for index, message in enumerate(history):

            date_time = ''
            if message.role == MessageRole.USER:
                date_time = self.get_date_time(
                    index = index,
                    history = history,
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
            system_prompt = self.get_system_instruction_use_case.invoke(
                info = user_for_ai_model,
            ),
        )

        return self.split_messages(response = ai_response)

    @staticmethod
    def get_date_time(
        history: list[SaveMessageModel],
        index: int,
        message: SaveMessageModel,
    ) -> str:

        previous_message = GenerateAiResponseUseCase.find_prev_user_message(
            history = history,
            index = index,
        )

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

            if prev_date != date and prev_time != time:
                date_time = f'{date} {time}'
            elif prev_date != date:
                date_time += f'{date} {time}'
            elif prev_time != time:
                date_time += f'{time}'

            if date_time:
                date_time = f'[{date_time}]'

        return date_time

    @staticmethod
    def find_prev_user_message(
        history: list[SaveMessageModel],
        index: int,
    ) -> SaveMessageModel | None:
        """
        Находит последнее USER сообщение перед указанным индексом.
        Оптимально по памяти (O(1)) и времени (O(n) в худшем случае).
        """
        # Защита от выхода за границы
        if not history or index <= 0:
            return None

        start_idx = min(index - 1, len(history) - 1)
        for i in range(start_idx, -1, -1):
            if history[i].role == MessageRole.USER:
                return history[i]

        return None

    @staticmethod
    def split_messages(
        response: str,
    ) -> List[str]:

        pattern = fr'\n|\n\n|{GenerateAiResponseUseCase.NEXT_MESSAGE_TAG_REGEX}'

        response_no_brackets = GenerateAiResponseUseCase\
            .replace_brackets_except_next(response)

        response_no_zero_no_tire = re\
            .sub(r'\b0\b', '', response_no_brackets)\
            .replace('—', '-')\
            .replace('–', '-')
        response_no_space = re\
            .sub(r' +', ' ', response_no_zero_no_tire)\
            .strip()

        lines: list[str] = re.split(pattern, response_no_space)

        logger.info(f'GenerateAiResponseUseCase.split_messages lines = {lines}')

        if not lines:
            logger.warning(
                f'GenerateAiResponseUseCase.split_messages: empty lines; '
                f'response = {response}',
            )
            return []

        result = []
        current = lines[0]

        for line in lines[1:]:
            if random() < 0.75:
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
