import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties

from bot.util.log_util import get_logger

class BotManager:

    def __init__(
        self,
        token: str,
        name: str,
    ):
        self.name = name
        self.bot = Bot(
            token = token,
            default = DefaultBotProperties(parse_mode = "HTML"),
        )
        self.dispatcher = Dispatcher()
        self._task: asyncio.Task | None = None

    async def _run(self):
        try:
            # Сигналы обрабатывает main (ShutdownSignal): у двух диспетчеров
            # обработчики aiogram перетирают друг друга, и останавливается только один.
            # Сессию закрывает close(), чтобы фоновые ответы успели отправиться.
            await self.dispatcher.start_polling(
                self.bot,
                handle_signals = False,
                close_bot_session = False,
            )
        except asyncio.CancelledError:
            print(f"{self.name}: polling cancelled")
            raise
        except Exception as e:
            print(f"{self.name}: polling error: {e}")

    async def start(self) -> bool:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run())
            _logger.info(f"{self.name}: started")
            return True
        else:
            _logger.info(f"{self.name}: start request failed")
            return False

    async def stop(self) -> bool:
        if self._task and not self._task.done():
            try:
                await self.dispatcher.stop_polling()
            except RuntimeError:
                # Задача создана, но polling ещё не успел запуститься
                _logger.info(f"{self.name}: polling not started yet, cancelling")
                self._task.cancel()
            _logger.info(f"{self.name}: stopped")
            return True
        else:
            return False

    async def close(self) -> None:
        await self.bot.session.close()
        _logger.info(f"{self.name}: session closed")


_logger = get_logger(BotManager.__name__)
