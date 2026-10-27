import asyncio

from bot.feature.business.domain.model.ChatStep import ChatStepPayload
from bot.feature.business.domain.repository.BotRepository import BotRepository
from bot.feature.business.domain.usecase.IsChatStepActualUseCase import \
    IsChatStepActualUseCase
from bot.feature.business.domain.usecase.SaveMessageUseCase import SaveMessageUseCase
from bot.feature.business.domain.util.HumanDelays import HumanDelays
from bot.util.log_util import get_logger


class SendAnswerMessageUseCase:
    """
    Отправка одного сообщения ответа: пауза «на набор», проверка талона, отправка, сохранение.
    Талон проверяется после паузы, прямо перед отправкой.
    """

    def __init__(
        self,
        bot_repository: BotRepository,
        is_chat_step_actual_use_case: IsChatStepActualUseCase,
        save_message_use_case: SaveMessageUseCase,
        human_delays: HumanDelays,
    ):
        self._bot = bot_repository
        self._is_actual = is_chat_step_actual_use_case
        self._save_message = save_message_use_case
        self._delays = human_delays

    async def invoke(
        self,
        payload: ChatStepPayload,
        text: str,
    ) -> bool:
        """False - талон устарел, сообщение не отправлено и остальные отправлять не нужно."""
        await asyncio.sleep(self._delays.write_message(text = text))

        if not await self._is_actual.invoke(ticket = payload.ticket):
            _logger.info("Шаг ответа устарел, не отправляю: chat_id=%s", payload.chat_id)
            return False

        try:
            sent = await self._bot.send_message(
                chat_id = payload.chat_id,
                business_connection_id = payload.context.business_connection_id,
                text = text,
            )
            # Сохраняем сразу: следующий ответ (после отмены) должен видеть уже отправленное
            if sent is not None:
                await self._save_message.invoke(save_message_model_list = [sent])
        except Exception:
            _logger.exception("Не удалось отправить сообщение: chat_id=%s", payload.chat_id)

        return True


_logger = get_logger(SendAnswerMessageUseCase.__name__)
