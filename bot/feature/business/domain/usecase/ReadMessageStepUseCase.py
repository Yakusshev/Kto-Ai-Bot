from bot.feature.business.domain.model.ChatDecision import ChatAction
from bot.feature.business.domain.model.ChatEvent import ChatEvent, ChatEventKind
from bot.feature.business.domain.model.ChatState import ChatPhase
from bot.feature.business.domain.model.ChatStep import ChatStepKind, ChatStepPayload
from bot.feature.business.domain.repository.BotRepository import BotRepository
from bot.feature.business.domain.repository.ChatStateRepository import \
    ChatStateRepository
from bot.feature.business.domain.usecase.ApplyChatEventUseCase import \
    ApplyChatEventUseCase
from bot.feature.business.domain.usecase.ScheduleChatStepUseCase import \
    ScheduleChatStepUseCase
from bot.util.log_util import get_logger


class ReadMessageStepUseCase:
    """
    Шаг «прочитать»: помечает прочитанным последнее накопленное сообщение,
    переводит чат из preparing в answering и планирует шаг «начать печатать».
    Талон проверен вызывающим (HandleChatStepUseCase) прямо перед шагом.
    """

    def __init__(
        self,
        bot_repository: BotRepository,
        chat_state_repository: ChatStateRepository,
        apply_chat_event_use_case: ApplyChatEventUseCase,
        schedule_chat_step_use_case: ScheduleChatStepUseCase,
    ):
        self._bot = bot_repository
        self._state_repository = chat_state_repository
        self._apply = apply_chat_event_use_case
        self._schedule = schedule_chat_step_use_case

    async def invoke(
        self,
        payload: ChatStepPayload,
    ) -> None:
        ticket = payload.ticket
        context = payload.context

        message_id = context.message_id
        if ticket.phase == ChatPhase.PREPARING:
            # Пока ждали, могли прийти ещё сообщения: «читаем» последнее
            state = await self._state_repository.get(chat_id = ticket.chat_id)
            if state.pending_message_ids:
                message_id = state.pending_message_ids[-1]

        if message_id is not None:
            await self._read(
                payload = payload,
                message_id = message_id,
            )

        answer_ticket = ticket
        if ticket.phase == ChatPhase.PREPARING:
            decision = await self._apply.invoke(
                chat_id = ticket.chat_id,
                event = ChatEvent(
                    kind = ChatEventKind.PREPARING_FINISHED,
                    ticket = ticket,
                ),
            )
            if decision.action != ChatAction.START_ANSWER:
                _logger.info("Шаг read устарел при переходе: chat_id=%s", ticket.chat_id)
                return
            answer_ticket = decision.state.ticket()

        await self._schedule.invoke(
            kind = ChatStepKind.START_TYPING,
            ticket = answer_ticket,
            context = context,
        )

    async def _read(
        self,
        payload: ChatStepPayload,
        message_id: int,
    ) -> None:
        try:
            await self._bot.read_message(
                chat_id = payload.chat_id,
                business_connection_id = payload.context.business_connection_id,
                message_id = message_id,
            )
        except Exception as e:
            # «Прочитано» - только внешний вид, ответу это не мешает
            _logger.warning("Не удалось отметить прочитанным: chat_id=%s, %s", payload.chat_id, e)


_logger = get_logger(ReadMessageStepUseCase.__name__)
