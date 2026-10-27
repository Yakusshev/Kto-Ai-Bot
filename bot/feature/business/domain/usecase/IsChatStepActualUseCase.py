from bot.feature.business.domain.model.ChatState import StepTicket
from bot.feature.business.domain.repository.ChatStateRepository import \
    ChatStateRepository


class IsChatStepActualUseCase:
    """
    Проверка отложенного шага (прочитать, начать печатать, отправить) перед действием.
    False - талон устарел (пришло новое сообщение или ответил владелец):
    шаг должен тихо завершиться.
    """

    def __init__(
        self,
        chat_state_repository: ChatStateRepository,
    ):
        self._repository = chat_state_repository

    async def invoke(
        self,
        ticket: StepTicket,
    ) -> bool:
        state = await self._repository.get(chat_id = ticket.chat_id)
        return state.is_actual(ticket)
