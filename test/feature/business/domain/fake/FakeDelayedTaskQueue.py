from bot.feature.business.domain.model.ChatStep import ChatStepPayload
from bot.feature.business.domain.repository.DelayedTaskQueue import DelayedTaskQueue


class FakeDelayedTaskQueue(DelayedTaskQueue):
    """Копит задачи вместо отправки: тест сам решает, какие и когда «доставить»."""

    def __init__(self) -> None:
        self.sent_list: list[tuple[ChatStepPayload, float | int]] = []

    @property
    def payload_list(self) -> list[ChatStepPayload]:
        return [payload for payload, _ in self.sent_list]

    async def send(
        self,
        task: ChatStepPayload,
        delay_seconds: float | int,
    ) -> None:
        self.sent_list.append((task, delay_seconds))
