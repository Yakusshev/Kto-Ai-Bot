from bot.feature.business.domain.model.ChatStep import ChatStepKind, ChatStepPayload
from bot.feature.business.domain.repository.BotRepository import BotRepository
from bot.feature.business.domain.usecase.ScheduleChatStepUseCase import \
    ScheduleChatStepUseCase
from bot.util.log_util import get_logger


class StartTypingStepUseCase:
    """
    Шаг «начать печатать»: показывает «печатает...» и планирует шаг генерации.
    Дальше «печатает...» держит сам шаг генерации (пока ждёт модель).
    """

    def __init__(
        self,
        bot_repository: BotRepository,
        schedule_chat_step_use_case: ScheduleChatStepUseCase,
    ):
        self._bot = bot_repository
        self._schedule = schedule_chat_step_use_case

    async def invoke(
        self,
        payload: ChatStepPayload,
    ) -> None:
        try:
            await self._bot.send_typing_chat_action(
                chat_id = payload.chat_id,
                business_connection_id = payload.context.business_connection_id,
            )
        except Exception as e:
            _logger.warning("Не удалось показать «печатает»: chat_id=%s, %s", payload.chat_id, e)

        await self._schedule.invoke(
            kind = ChatStepKind.GENERATE_AND_SEND,
            ticket = payload.ticket,
            context = payload.context,
        )


_logger = get_logger(StartTypingStepUseCase.__name__)
