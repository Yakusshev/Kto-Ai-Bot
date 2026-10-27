from bot.feature.business.domain.model.ChatStep import ChatStepKind, ChatStepPayload
from bot.feature.business.domain.usecase.GenerateAndSendStepUseCase import \
    GenerateAndSendStepUseCase
from bot.feature.business.domain.usecase.IsChatStepActualUseCase import \
    IsChatStepActualUseCase
from bot.feature.business.domain.usecase.ReadMessageStepUseCase import \
    ReadMessageStepUseCase
from bot.feature.business.domain.usecase.StartTypingStepUseCase import \
    StartTypingStepUseCase
from bot.feature.business.domain.util.InFlightStepRegistry import InFlightStepRegistry
from bot.util.log_util import get_logger


class HandleChatStepUseCase:
    """
    Обработка отложенного шага, полученного из очереди (любым транспортом).

    Идемпотентна при повторной доставке: дубль выполняющегося шага пропускается
    (InFlightStepRegistry), а шаг, чей талон устарел (уже выполнен, пришло новое сообщение,
    ответил владелец), тихо завершается без действий.
    """

    def __init__(
        self,
        in_flight_step_registry: InFlightStepRegistry,
        is_chat_step_actual_use_case: IsChatStepActualUseCase,
        read_message_step_use_case: ReadMessageStepUseCase,
        start_typing_step_use_case: StartTypingStepUseCase,
        generate_and_send_step_use_case: GenerateAndSendStepUseCase,
    ):
        self._registry = in_flight_step_registry
        self._is_actual = is_chat_step_actual_use_case
        self._read = read_message_step_use_case
        self._start_typing = start_typing_step_use_case
        self._generate_and_send = generate_and_send_step_use_case

    async def invoke(
        self,
        payload: ChatStepPayload,
    ) -> None:
        if not self._registry.try_acquire(step_id = payload.step_id):
            _logger.info("Шаг уже выполняется, дубль пропущен: %s", payload.step_id)
            return

        try:
            if not await self._is_actual.invoke(ticket = payload.ticket):
                _logger.info(
                    "Шаг %s устарел, пропускаю: chat_id=%s",
                    payload.kind, payload.chat_id,
                )
                return

            match payload.kind:
                case ChatStepKind.READ_MESSAGE:
                    await self._read.invoke(payload = payload)
                case ChatStepKind.START_TYPING:
                    await self._start_typing.invoke(payload = payload)
                case ChatStepKind.GENERATE_AND_SEND:
                    await self._generate_and_send.invoke(payload = payload)
        finally:
            self._registry.release(step_id = payload.step_id)


_logger = get_logger(HandleChatStepUseCase.__name__)
