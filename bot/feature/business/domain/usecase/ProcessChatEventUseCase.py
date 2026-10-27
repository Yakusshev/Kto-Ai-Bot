from bot.feature.business.domain.model.ChatDecision import ChatAction
from bot.feature.business.domain.model.ChatEvent import ChatEvent
from bot.feature.business.domain.model.ChatStep import ChatStepContext, ChatStepKind
from bot.feature.business.domain.usecase.ApplyChatEventUseCase import \
    ApplyChatEventUseCase
from bot.feature.business.domain.usecase.ScheduleChatStepUseCase import \
    ScheduleChatStepUseCase

# Какой шаг запускает действие перехода; остальные действия шагов не требуют
_FIRST_STEP_BY_ACTION = {
    ChatAction.START_PREPARING: ChatStepKind.READ_MESSAGE,
    ChatAction.CANCEL_AND_ANSWER_NOW: ChatStepKind.READ_MESSAGE,
    ChatAction.START_ANSWER: ChatStepKind.GENERATE_AND_SEND,
}


class ProcessChatEventUseCase:
    """
    Вход из обработчиков: применяет событие (сообщение, ответ владельца, напоминание)
    к состоянию чата и по решению планирует первый шаг ответа.
    Отмена прежнего ответа - это новый талон: шаги со старым талоном тихо завершатся.
    """

    def __init__(
        self,
        apply_chat_event_use_case: ApplyChatEventUseCase,
        schedule_chat_step_use_case: ScheduleChatStepUseCase,
    ):
        self._apply = apply_chat_event_use_case
        self._schedule = schedule_chat_step_use_case

    async def invoke(
        self,
        chat_id: int,
        event: ChatEvent,
        context: ChatStepContext | None = None,
    ) -> ChatAction:
        decision = await self._apply.invoke(
            chat_id = chat_id,
            event = event,
        )

        kind = _FIRST_STEP_BY_ACTION.get(decision.action)
        if kind is not None:
            if context is None:
                raise ValueError(f"Для действия {decision.action} нужен контекст шага")
            await self._schedule.invoke(
                kind = kind,
                ticket = decision.state.ticket(),
                context = context,
            )

        return decision.action
