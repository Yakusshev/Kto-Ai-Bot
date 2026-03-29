import asyncio
import datetime
from random import random

from bot.feature.business.data.repository.BotRepositoryImpl import BotRepositoryImpl
from bot.util.log_util import get_logger


class TypingLoopUseCase:

    def __init__(
        self,
        bot_repository: BotRepositoryImpl,
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
        Иногда делает паузу 1-3 сек (имитирует «задумался»).
        """

        default_pause = 7

        start_typing_time = datetime.datetime.now()

        while not stop_event.is_set():

            delta = datetime.datetime.now() - start_typing_time

            if delta.seconds > random.uniform(15, 20):
                break

            try:
                await self.bot_repository.send_typing_chat_action(
                    chat_id = chat_id,
                    business_connection_id = business_connection_id,
                )
            except Exception as e:
                logger.warning("typing_loop ошибка send_chat_action: %s", e)

            await asyncio.sleep(default_pause + random.uniform(1, 5))


logger = get_logger(TypingLoopUseCase.__name__)