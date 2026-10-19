import asyncio
import signal

from bot.util.log_util import get_logger

SHUTDOWN_SIGNAL_LIST = (signal.SIGTERM, signal.SIGINT)


class ShutdownSignal:
    """
    Единая точка обработки SIGTERM/SIGINT для всего процесса.

    Сигнал только взводит событие: сама остановка выполняется в main,
    чтобы успеть дождаться ответов в процессе и закрыть соединения.
    """

    def __init__(self):
        self._event = asyncio.Event()

    def install(self, loop: asyncio.AbstractEventLoop) -> None:
        for sig in SHUTDOWN_SIGNAL_LIST:
            try:
                loop.add_signal_handler(
                    sig,
                    self._on_signal,
                    sig,
                )
            except NotImplementedError:
                # Windows: Ctrl+C придёт как KeyboardInterrupt, asyncio.run
                # отменит main, и остановка выполнится в его finally
                _logger.warning(f"Обработчик сигнала {sig.name} не поддерживается")

    async def wait(self) -> None:
        await self._event.wait()

    def _on_signal(self, sig: signal.Signals) -> None:
        if self._event.is_set():
            _logger.warning(f"Получен {sig.name}: остановка уже выполняется")
        else:
            _logger.info(f"Получен {sig.name}: начинаю остановку")
            self._event.set()


_logger = get_logger(ShutdownSignal.__name__)
