import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties


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
        self._task = None

    async def _run(self):
        try:
            await self.dispatcher.start_polling(self.bot)
        except asyncio.CancelledError:
            print(f"{self.name}: polling cancelled")
            raise
        except Exception as e:
            print(f"{self.name}: polling error: {e}")

    async def start(self) -> bool:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run())
            print(f"{self.name}: started")
            return True
        else:
            return False

    async def stop(self):
        if self._task and not self._task.done():
            await self.dispatcher.stop_polling()
            return True
        else:
            return False
            # self._task.cancel()
            # await self._task
