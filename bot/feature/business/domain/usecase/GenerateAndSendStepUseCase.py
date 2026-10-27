import asyncio

from bot.feature.business.domain.model.ChatEvent import ChatEvent, ChatEventKind
from bot.feature.business.domain.model.ChatStep import ChatStepPayload
from bot.feature.business.domain.model.UserMessageInfoForAiModel import \
    UserMessageInfoForAiModel
from bot.feature.business.domain.repository.BotRepository import BotRepository
from bot.feature.business.domain.scenario.GenerateAiReponseScenario import \
    GenerateAiResponseScenario
from bot.feature.business.domain.usecase.ApplyChatEventUseCase import \
    ApplyChatEventUseCase
from bot.feature.business.domain.usecase.SendAnswerMessageUseCase import \
    SendAnswerMessageUseCase
from bot.feature.business.domain.usecase.TypingLoopUseCase import TypingLoopUseCase
from bot.util.log_util import get_logger

TYPING_STOP_TIMEOUT_SECONDS = 5


class GenerateAndSendStepUseCase:
    """
    Шаг «сгенерировать и отправить».

    «Печатает...» держится внутри шага, пока ждём модель, и всегда останавливается
    в finally. Талон проверяется перед каждой отправкой (после паузы «на набор»):
    если пришло новое сообщение или ответил владелец, шаг тихо завершается.

    Шаг не бросает исключений наружу (кроме отмены задачи): повторная доставка
    после частичной отправки дала бы двойной ответ. Ошибка модели или отправки
    логируется, чат возвращается в idle.
    """

    def __init__(
        self,
        bot_repository: BotRepository,
        generate_ai_response_scenario: GenerateAiResponseScenario,
        typing_loop_use_case: TypingLoopUseCase,
        send_answer_message_use_case: SendAnswerMessageUseCase,
        apply_chat_event_use_case: ApplyChatEventUseCase,
    ):
        self._bot = bot_repository
        self._scenario = generate_ai_response_scenario
        self._typing_loop = typing_loop_use_case
        self._send_answer = send_answer_message_use_case
        self._apply = apply_chat_event_use_case

    async def invoke(
        self,
        payload: ChatStepPayload,
    ) -> None:
        stop_typing = asyncio.Event()
        typing_task = asyncio.create_task(
            self._typing_loop.invoke(
                chat_id = payload.chat_id,
                business_connection_id = payload.context.business_connection_id,
                stop_event = stop_typing,
            ),
        )

        try:
            await self._generate_and_send(payload = payload)
        except Exception:
            _logger.exception("Ошибка шага ответа: chat_id=%s", payload.chat_id)
        finally:
            await self._stop_typing(
                stop_typing = stop_typing,
                typing_task = typing_task,
            )

        await self._finish(payload = payload)

    async def _generate_and_send(
        self,
        payload: ChatStepPayload,
    ) -> None:
        context = payload.context

        answer_list = await self._scenario.invoke(
            user_for_ai_model = UserMessageInfoForAiModel(
                chat_id = payload.chat_id,
                username = context.username,
                full_name = context.full_name,
                datetime = context.message_datetime,
            ),
            owner_model = await self._bot.get_business_connection_owner(
                id = context.business_connection_id,
            ),
            remind = context.remind,
        )

        for answer in answer_list:
            if not answer:
                continue

            is_sent = await self._send_answer.invoke(
                payload = payload,
                text = answer,
            )
            if not is_sent:
                return

    @staticmethod
    async def _stop_typing(
        stop_typing: asyncio.Event,
        typing_task: asyncio.Task[None],
    ) -> None:
        stop_typing.set()
        # wait не пробрасывает отмену самой задачи typing и не прячет отмену шага
        _, pending = await asyncio.wait({typing_task}, timeout = TYPING_STOP_TIMEOUT_SECONDS)
        for task in pending:
            task.cancel()

    async def _finish(
        self,
        payload: ChatStepPayload,
    ) -> None:
        try:
            await self._apply.invoke(
                chat_id = payload.chat_id,
                event = ChatEvent(
                    kind = ChatEventKind.ANSWER_FINISHED,
                    ticket = payload.ticket,
                ),
            )
        except Exception:
            # Состояние само исправится при следующем сообщении; не бросаем,
            # чтобы повторная доставка не ответила второй раз
            _logger.exception("Не удалось завершить ответ: chat_id=%s", payload.chat_id)


_logger = get_logger(GenerateAndSendStepUseCase.__name__)
