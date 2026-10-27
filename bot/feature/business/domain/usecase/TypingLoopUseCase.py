import asyncio
import datetime
import random

from bot.feature.business.domain.repository.BotRepository import BotRepository
from bot.util.log_util import get_logger

DEFAULT_PAUSE_SECONDS = 7
MAX_TYPING_RANGE_SECONDS = (15, 20)


class TypingLoopUseCase:

    def __init__(
        self,
        bot_repository: BotRepository,
    ):
        self.bot_repository = bot_repository

    async def invoke(
        self,
        chat_id: int,
        business_connection_id: str,
        stop_event: asyncio.Event,
    ) -> None:
        """
        Поддерживает статус «печатает...» пока не выставлен stop_event.
        Между действиями ждёт паузу 8-12 сек, но просыпается сразу по stop_event,
        поэтому после остановки новых «печатает» не будет.
        """

        start_typing_time = datetime.datetime.now()

        while not stop_event.is_set():

            delta = datetime.datetime.now() - start_typing_time

            if delta.seconds > random.uniform(
                a = MAX_TYPING_RANGE_SECONDS[0],
                b = MAX_TYPING_RANGE_SECONDS[1],
            ):
                break

            try:
                await self.bot_repository.send_typing_chat_action(
                    chat_id = chat_id,
                    business_connection_id = business_connection_id,
                )
            except Exception as e:
                logger.warning("typing_loop ошибка send_chat_action: %s", e)

            pause = DEFAULT_PAUSE_SECONDS + random.uniform(a = 1, b = 5)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout = pause)
            except asyncio.TimeoutError:
                pass


logger = get_logger(TypingLoopUseCase.__name__)
