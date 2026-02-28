from random import random
from typing import List

from bot.data.repository.ChatHistoryRepositoryImpl import ChatHistoryRepositoryImpl
from bot.domain.DefaultSystemInstuction import anya_system_instruction
from bot.domain.model.MessageForAiModel import MessageForAiModel
from bot.domain.model.SaveMessageModel import SaveMessageModel
from bot.domain.model.UserInfoForAiModel import UserInfoForAiModel
from bot.domain.repository.AiRepository import AiRepository


class GenerateAiResponseUseCase:
    DATE_FORMAT = "%d.%m"
    TIME_FORMAT = "%H:%M"

    def __init__(
        self,
        llm_repository: AiRepository,
        session_repository: ChatHistoryRepositoryImpl,
    ):
        self.llm_repository = llm_repository
        self.session_repository = session_repository

    async def invoke(
        self,
        user_message_model: UserInfoForAiModel,
    ) -> List[str]:

        history: List[SaveMessageModel] = await self.session_repository \
            .get_session_data(chat_id = user_message_model.id)

        ai_list: List[MessageForAiModel] = []

        for index, message in enumerate(history):

            date_time = ''

            date = message.created_at \
                .strftime(format = GenerateAiResponseUseCase.DATE_FORMAT)
            time = message.created_at \
                .strftime(format = GenerateAiResponseUseCase.TIME_FORMAT)

            if index > 0:
                previous_message = history[index - 1]
                prev_date = previous_message.created_at.strftime("%d.%m")
                prev_time = previous_message.created_at.strftime("%d.%m")

                if prev_date != date:
                    date_time += f'{date}'
                if prev_time != time:
                    date_time = f'{date_time} {time}'

                if date_time:
                    date_time = f'[{date_time}]'
            else:
                date_time = f'[{date} {time}]'

            if ai_list and ai_list[-1].role == message.role:

                previous_ai_message = ai_list[-1]

                ai_list[-1] = MessageForAiModel(
                    role = message.role,
                    content = f'{previous_ai_message.content}'
                              f'[next]'
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
            ),
        )

        return self.split_messages(response = ai_response)

    @staticmethod
    def split_messages(
        response: str,
    ) -> List[str]:

        lines = response.split('\n')
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
