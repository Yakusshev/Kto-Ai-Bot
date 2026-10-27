from datetime import datetime, timezone
from unittest.mock import AsyncMock

from bot.feature.business.domain.model.ChatEvent import ChatEvent, ChatEventKind
from bot.feature.business.domain.model.ChatStep import ChatStepContext, ChatStepPayload
from bot.feature.business.domain.scenario.GenerateAiReponseScenario import \
    GenerateAiResponseScenario
from bot.feature.business.domain.usecase.ApplyChatEventUseCase import \
    ApplyChatEventUseCase
from bot.feature.business.domain.usecase.DecideChatTransitionUseCase import \
    DecideChatTransitionUseCase
from bot.feature.business.domain.usecase.GenerateAndSendStepUseCase import \
    GenerateAndSendStepUseCase
from bot.feature.business.domain.usecase.HandleChatStepUseCase import \
    HandleChatStepUseCase
from bot.feature.business.domain.usecase.IsChatStepActualUseCase import \
    IsChatStepActualUseCase
from bot.feature.business.domain.usecase.ProcessChatEventUseCase import \
    ProcessChatEventUseCase
from bot.feature.business.domain.usecase.ReadMessageStepUseCase import \
    ReadMessageStepUseCase
from bot.feature.business.domain.usecase.SaveMessageUseCase import SaveMessageUseCase
from bot.feature.business.domain.usecase.ScheduleChatStepUseCase import \
    ScheduleChatStepUseCase
from bot.feature.business.domain.usecase.SendAnswerMessageUseCase import \
    SendAnswerMessageUseCase
from bot.feature.business.domain.usecase.StartTypingStepUseCase import \
    StartTypingStepUseCase
from bot.feature.business.domain.usecase.TypingLoopUseCase import TypingLoopUseCase
from bot.feature.business.domain.util.HumanDelays import HumanDelays
from bot.feature.business.domain.util.InFlightStepRegistry import InFlightStepRegistry
from bot.feature.business.domain.repository.ChatStateRepository import \
    ChatStateRepository
from .FakeBotRepository import FakeBotRepository
from .FakeChatStateRepository import FakeChatStateRepository
from .FakeDelayedTaskQueue import FakeDelayedTaskQueue

CHAT_ID = 7


def make_context(
    message_id: int | None = 1,
    text: str = "привет",
    remind: bool = False,
) -> ChatStepContext:
    return ChatStepContext(
        business_connection_id = "conn",
        username = "user",
        full_name = "User Name",
        message_datetime = datetime(2026, 1, 1, tzinfo = timezone.utc),
        message_text = text,
        message_id = message_id,
        remind = remind,
    )


class ChatStepHarness:
    """Собирает use case шагов на фейках: состояние, очередь, бот, генерация."""

    def __init__(
        self,
        state_repository: ChatStateRepository | None = None,
        is_instant: bool = True,
    ) -> None:
        self._delivered = 0
        self.state_repository = state_repository or FakeChatStateRepository()
        self.queue = FakeDelayedTaskQueue()
        self.bot = FakeBotRepository()
        self.answer_list = ["ответ"]
        self.scenario = AsyncMock(spec = GenerateAiResponseScenario)
        self.scenario.invoke.side_effect = self._generate
        self.save_message = AsyncMock(spec = SaveMessageUseCase)

        delays = HumanDelays(is_instant = is_instant)
        apply_event = ApplyChatEventUseCase(
            chat_state_repository = self.state_repository,
            decide_chat_transition_use_case = DecideChatTransitionUseCase(),
        )
        is_actual = IsChatStepActualUseCase(chat_state_repository = self.state_repository)
        schedule = ScheduleChatStepUseCase(
            delayed_task_queue = self.queue,
            human_delays = delays,
        )
        self.process_event = ProcessChatEventUseCase(
            apply_chat_event_use_case = apply_event,
            schedule_chat_step_use_case = schedule,
        )
        self.typing_loop = TypingLoopUseCase(bot_repository = self.bot)
        self.handle_step = HandleChatStepUseCase(
            in_flight_step_registry = InFlightStepRegistry(),
            is_chat_step_actual_use_case = is_actual,
            read_message_step_use_case = ReadMessageStepUseCase(
                bot_repository = self.bot,
                chat_state_repository = self.state_repository,
                apply_chat_event_use_case = apply_event,
                schedule_chat_step_use_case = schedule,
            ),
            start_typing_step_use_case = StartTypingStepUseCase(
                bot_repository = self.bot,
                schedule_chat_step_use_case = schedule,
            ),
            generate_and_send_step_use_case = GenerateAndSendStepUseCase(
                bot_repository = self.bot,
                generate_ai_response_scenario = self.scenario,
                typing_loop_use_case = self.typing_loop,
                send_answer_message_use_case = SendAnswerMessageUseCase(
                    bot_repository = self.bot,
                    is_chat_step_actual_use_case = is_actual,
                    save_message_use_case = self.save_message,
                    human_delays = delays,
                ),
                apply_chat_event_use_case = apply_event,
            ),
        )

    async def _generate(self, **kwargs) -> list[str]:
        return list(self.answer_list)

    async def user_message(
        self,
        message_id: int,
        text: str = "привет",
    ) -> None:
        await self.process_event.invoke(
            chat_id = CHAT_ID,
            event = ChatEvent(kind = ChatEventKind.USER_MESSAGE, message_id = message_id),
            context = make_context(message_id = message_id, text = text),
        )

    async def owner_message(self) -> None:
        await self.process_event.invoke(
            chat_id = CHAT_ID,
            event = ChatEvent(kind = ChatEventKind.OWNER_MESSAGE, message_id = 99),
        )

    async def run_next(self) -> ChatStepPayload:
        """Доставляет самую раннюю из ожидающих задач (очередь FIFO)."""
        payload = self.queue.payload_list[self._delivered]
        self._delivered += 1
        await self.handle_step.invoke(payload = payload)
        return payload

    async def run_all(self) -> None:
        while self._delivered < len(self.queue.payload_list):
            await self.run_next()
