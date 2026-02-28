from random import random
from typing import List

from bot.data.repository.ChatHistoryRepositoryImpl import ChatHistoryRepositoryImpl
from bot.domain.DefaultSystemInstuction import anyaSystemInstruction
from bot.domain.model.MessageForAiModel import MessageForAiModel
from bot.domain.repository.AiRepository import AiRepository

ROLE_TITLE = 'role'
ROLE_ASSISTANT = 'assistant'
ROLE_MODEL = 'model'
ROLE_USER = 'user'
CONTENT = 'content'

class GenerateAiResponseUseCase:

    def __init__(
        self,
        llm_repository: AiRepository,
        session_repository: ChatHistoryRepositoryImpl,
    ):
        self.llm_repository = llm_repository
        self.session_repository = session_repository

    async def invoke(
        self,
        user_message_model: MessageForAiModel,
    ) -> List[str]:
        messages_history = await self.session_repository.get_session_data(
            chat_id = user_message_model.id,
        )

        request_messages = []

        for msg in messages_history:
            role = ROLE_ASSISTANT if msg[ROLE_TITLE] == ROLE_MODEL else msg[ROLE_TITLE]

            if request_messages and request_messages[-1][ROLE_TITLE] == role:
                request_messages[-1][CONTENT] += "\n" + msg[CONTENT]
            else:
                request_messages.append({ROLE_TITLE: role, CONTENT: msg[CONTENT]})

        ai_response = await self.llm_repository.generate_response(
            messages = request_messages,
            system_prompt = anyaSystemInstruction(
                user_nickname = user_message_model.username
            )
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
