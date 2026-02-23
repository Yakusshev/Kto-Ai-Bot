from bot.data.repository.SessionRepository import SessionRepository
from bot.domain.DefaultSystemInstuction import anyaSystemInstruction
from bot.domain.model.UserMessageModel import UserMessageModel
from bot.domain.repository.LLMRepository import LLMRepository

ROLE_TITLE = 'role'
ROLE_ASSISTANT = 'assistant'
ROLE_MODEL = 'model'
ROLE_USER = 'user'
CONTENT = 'content'

class GenerateAiResponseUseCase:

    def __init__(
        self,
        llm_repository: LLMRepository,
        session_repository: SessionRepository,
    ):
        self.llm_repository = llm_repository
        self.session_repository = session_repository

    async def invoke(
        self,
        user_message_model: UserMessageModel,
    ) -> str:
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

        request_messages.append({ROLE_TITLE: ROLE_USER, CONTENT: user_message_model.content})

        return await self.llm_repository.generate_response(
            messages = request_messages,
            system_prompt = anyaSystemInstruction(
                user_nickname = user_message_model.username
            )
        )