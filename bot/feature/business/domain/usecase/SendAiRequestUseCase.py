from typing import List

from bot.feature.business.data.repository.ChatHistoryRepositoryImpl import \
    ChatHistoryRepositoryImpl
from bot.feature.business.domain.model.MessageForAiModel import MessageForAiModel
from bot.feature.business.domain.model.SaveMessageModel import SaveMessageModel, \
    MessageRole
from bot.feature.business.domain.model.UserMessageInfoForAiModel import \
    UserMessageInfoForAiModel
from bot.feature.business.domain.repository.AiRepository import AiRepository
from bot.feature.business.domain.usecase.GetSystemInstructionUseCase import \
    GetSystemInstructionUseCase


class SendAiRequestUseCase:
    NEXT_MESSAGE_TAG = '[next]'
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
        user_for_ai_model: UserMessageInfoForAiModel,
        system_prompt: str,
    ) -> str:

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
                              f'{SendAiRequestUseCase.NEXT_MESSAGE_TAG}'
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
            system_prompt = system_prompt,
        )

        return ai_response

    @staticmethod
    def get_date_time(
        history: list[SaveMessageModel],
        index: int,
        message: SaveMessageModel,
    ) -> str:

        previous_message = SendAiRequestUseCase.find_prev_user_message(
            history = history,
            index = index,
        )

        date_time = ''

        date = message.created_at \
            .strftime(format = SendAiRequestUseCase.DATE_FORMAT)
        time = message.created_at \
            .strftime(format = SendAiRequestUseCase.TIME_FORMAT)

        if previous_message is None:
            date_time = f'[{date} {time}]'
        else:
            prev_date = previous_message \
                .created_at \
                .strftime(format = SendAiRequestUseCase.DATE_FORMAT)
            prev_time = previous_message \
                .created_at \
                .strftime(format = SendAiRequestUseCase.TIME_FORMAT)

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
