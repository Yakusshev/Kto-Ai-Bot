from dishka import AsyncContainer, Provider, Scope, provide, provide_all

from bot.core.domain.const.env_const import (
    DEBUG_MODE_TYPING,
    DELAYED_QUEUE_BACKEND,
    SQS_ACCESS_KEY_ID,
    SQS_ENDPOINT,
    SQS_QUEUE_URL,
    SQS_REGION,
    SQS_SECRET_ACCESS_KEY,
)
from bot.feature.business.data.queue.InMemoryDelayedTaskQueue import \
    InMemoryDelayedTaskQueue
from bot.feature.business.data.queue.SqsDelayedTaskQueue import (
    SqsConfig,
    SqsDelayedTaskQueue,
    create_sqs_client,
)
from bot.feature.business.domain.model.ChatStep import ChatStepPayload
from bot.feature.business.domain.repository.DelayedTaskQueue import DelayedTaskQueue
from bot.feature.business.domain.usecase.GenerateAndSendStepUseCase import \
    GenerateAndSendStepUseCase
from bot.feature.business.domain.usecase.HandleChatStepUseCase import \
    HandleChatStepUseCase
from bot.feature.business.domain.usecase.ProcessChatEventUseCase import \
    ProcessChatEventUseCase
from bot.feature.business.domain.usecase.ReadMessageStepUseCase import \
    ReadMessageStepUseCase
from bot.feature.business.domain.usecase.ScheduleChatStepUseCase import \
    ScheduleChatStepUseCase
from bot.feature.business.domain.usecase.SendAnswerMessageUseCase import \
    SendAnswerMessageUseCase
from bot.feature.business.domain.usecase.StartTypingStepUseCase import \
    StartTypingStepUseCase
from bot.feature.business.domain.util.HumanDelays import HumanDelays
from bot.feature.business.domain.util.InFlightStepRegistry import InFlightStepRegistry

BACKEND_SQS = "sqs"


class ChatStepProvider(Provider):
    """
    Отложенные шаги ответа (прочитал / печатает / отправил) и очередь для них.
    Адаптер очереди выбирает DELAYED_QUEUE_BACKEND: memory (по умолчанию) или sqs.
    """

    # Общее для всех апдейтов: реестр выполняющихся шагов
    in_flight_step_registry = provide(InFlightStepRegistry, scope = Scope.APP)

    @provide(scope = Scope.APP)
    def get_human_delays(self) -> HumanDelays:
        # DEBUG_MODE_TYPING отключает паузы
        return HumanDelays(is_instant = DEBUG_MODE_TYPING)

    @provide(scope = Scope.APP)
    def get_delayed_task_queue(
        self,
        container: AsyncContainer,
    ) -> DelayedTaskQueue:
        if DELAYED_QUEUE_BACKEND == BACKEND_SQS:
            return SqsDelayedTaskQueue(
                client = create_sqs_client(
                    config = SqsConfig(
                        endpoint = SQS_ENDPOINT,
                        region = SQS_REGION,
                        access_key_id = SQS_ACCESS_KEY_ID,
                        secret_access_key = SQS_SECRET_ACCESS_KEY,
                        queue_url = SQS_QUEUE_URL,
                    ),
                ),
                queue_url = SQS_QUEUE_URL,
            )

        async def run_step(payload: ChatStepPayload) -> None:
            # Каждый шаг - в своём REQUEST-скоупе (Strings и др.), как у приёмника очереди
            async with container() as request_container:
                handle_step = await request_container.get(HandleChatStepUseCase)
                await handle_step.invoke(payload = payload)

        return InMemoryDelayedTaskQueue(handler = run_step)

    step_use_case_layer = provide_all(
        ScheduleChatStepUseCase,
        ProcessChatEventUseCase,
        ReadMessageStepUseCase,
        StartTypingStepUseCase,
        SendAnswerMessageUseCase,
        GenerateAndSendStepUseCase,
        HandleChatStepUseCase,
        scope = Scope.REQUEST,
    )
