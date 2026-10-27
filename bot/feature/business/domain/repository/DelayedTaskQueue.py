from abc import ABC, abstractmethod

from bot.feature.business.domain.model.ChatStep import ChatStepPayload

# Предел задержки сообщения SQS-совместимой очереди (Yandex Message Queue): DelaySeconds <= 900
MAX_DELAY_SECONDS = 900


class DelayedTaskQueue(ABC):
    """
    Очередь отложенных шагов ответа.

    Доставка «минимум один раз»: шаг может прийти повторно, поэтому обработчик
    сверяет талон шага и ничего не делает, если он устарел.
    """

    @abstractmethod
    async def send(
        self,
        task: ChatStepPayload,
        delay_seconds: float | int,
    ) -> None:
        """
        Ставит шаг в очередь: он будет доставлен обработчику не раньше чем через
        delay_seconds. Задержка выше MAX_DELAY_SECONDS обрезается до предела очереди.
        """
        pass

    async def shutdown(self) -> None:
        """Штатная остановка: адаптеры с собственным исполнением дожидаются запущенных шагов."""
        return None
