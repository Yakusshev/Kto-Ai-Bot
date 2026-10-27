import asyncio
from typing import AsyncIterator
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
import ydb
from aiogram_i18n import I18nContext
from dishka import AsyncContainer, Provider, Scope, make_async_container, provide

from bot.core.di.StandaloneI18nProvider import StandaloneI18nProvider
from bot.core.di.container import create_container
from bot.feature.admin.domain.scenario.GetRemindInfoTextScenario import \
    GetRemindInfoTextScenario
from bot.feature.business.data.datasource.TelegramRemoteDataSource import \
    TelegramRemoteDataSource
from bot.feature.business.domain.repository.DelayedTaskQueue import DelayedTaskQueue
from bot.feature.business.domain.usecase.HandleChatStepUseCase import \
    HandleChatStepUseCase
from bot.feature.business.domain.repository.AiRepository import AiRepository
from bot.feature.business.entrypoint.service.ChatService import ChatService
from bot.feature.business.entrypoint.service.ReminderService import ReminderService
from bot.feature.business.domain.model.ChatState import ChatPhase, StepTicket
from bot.feature.business.domain.model.ChatStep import ChatStepKind, ChatStepPayload
from bot.feature.business.domain.repository.ChatStateRepository import \
    ChatStateRepository
from bot.resource.Strings import Strings
from feature.business.domain.fake.ChatStepHarness import make_context
from feature.business.domain.fake.FakeChatStateRepository import \
    FakeChatStateRepository

CORE_PROVIDER = 'bot.core.di.CoreProvider'
REAL_SESSION_POOL = ydb.SessionPool


def _fake_i18n_context() -> I18nContext:
    i18n = MagicMock(spec = I18nContext)
    i18n.locale = "ru"
    return i18n


class FakeBoundariesProvider(Provider):
    """Подменяет внешние границы: YDB, Telegram, LLM и I18n."""

    scope = Scope.APP

    @provide(override = True)
    def get_driver(self) -> ydb.Driver:
        return MagicMock(spec = ydb.Driver)

    @provide(override = True)
    def get_session_pool(self) -> ydb.SessionPool:
        return MagicMock(spec = ydb.SessionPool)

    @provide(override = True)
    def get_telegram_remote_data_source(self) -> TelegramRemoteDataSource:
        return MagicMock(spec = TelegramRemoteDataSource)

    @provide(override = True)
    def get_ai_repository(self) -> AiRepository:
        return MagicMock(spec = AiRepository)

    @provide(override = True, scope = Scope.REQUEST)
    def get_i18n_context(self) -> I18nContext:
        return _fake_i18n_context()


class TestContainerWithoutAiogram:

    @pytest_asyncio.fixture
    async def container(self) -> AsyncIterator[AsyncContainer]:
        container = create_container(FakeBoundariesProvider())
        yield container
        await container.close()

    @pytest.mark.asyncio
    async def test_when_request_chat_service_expect_instance_without_update(
        self,
        container: AsyncContainer,
    ):
        async with container() as request_container:
            actual = await request_container.get(ChatService)

        assert isinstance(actual, ChatService)

    @pytest.mark.asyncio
    async def test_when_request_reminder_service_expect_instance_without_update(
        self,
        container: AsyncContainer,
    ):
        async with container() as request_container:
            actual = await request_container.get(ReminderService)

        assert isinstance(actual, ReminderService)

    @pytest.mark.asyncio
    async def test_when_request_admin_scenario_expect_instance(
        self,
        container: AsyncContainer,
    ):
        async with container() as request_container:
            actual = await request_container.get(GetRemindInfoTextScenario)

        assert isinstance(actual, GetRemindInfoTextScenario)

    @pytest.mark.asyncio
    async def test_when_two_requests_expect_new_strings_each_time(
        self,
        container: AsyncContainer,
    ):
        async with container() as first_request:
            first = await first_request.get(Strings)
        async with container() as second_request:
            second = await second_request.get(Strings)

        assert first is not second

    @pytest.mark.asyncio
    async def test_when_two_requests_expect_same_delayed_task_queue(
        self,
        container: AsyncContainer,
    ):
        async with container() as first_request:
            first = await first_request.get(DelayedTaskQueue)
            first_reminder = await first_request.get(ReminderService)
        async with container() as second_request:
            second = await second_request.get(DelayedTaskQueue)

        assert first is second
        assert first_reminder.process_chat_event_use_case is not None

    @pytest.mark.asyncio
    async def test_when_request_step_handler_expect_instance(
        self,
        container: AsyncContainer,
    ):
        async with container() as request_container:
            actual = await request_container.get(HandleChatStepUseCase)

        assert isinstance(actual, HandleChatStepUseCase)


class SpyStateProvider(Provider):
    """Подменяет хранилище состояния фейком: видно, что шаг дошёл до проверки талона."""

    scope = Scope.APP

    def __init__(self, repository: FakeChatStateRepository):
        super().__init__()
        self._repository = repository

    @provide(override = True)
    def get_chat_state_repository(self) -> ChatStateRepository:
        return self._repository


class TestInMemoryQueueWiring:

    @pytest.mark.asyncio
    async def test_when_step_sent_to_default_queue_expect_handled_in_request_scope(self):
        repository = FakeChatStateRepository()
        seen: list[int] = []
        original_get = repository.get

        async def spy_get(chat_id: int):
            seen.append(chat_id)
            return await original_get(chat_id)

        repository.get = spy_get  # type: ignore[method-assign]
        container = create_container(FakeBoundariesProvider(), SpyStateProvider(repository))

        queue = await container.get(DelayedTaskQueue)
        await queue.send(
            task = ChatStepPayload(
                step_id = "s1",
                kind = ChatStepKind.READ_MESSAGE,
                ticket = StepTicket(chat_id = 77, phase = ChatPhase.PREPARING, phase_version = 1),
                context = make_context(),
            ),
            delay_seconds = 0,
        )
        await asyncio.sleep(0.1)
        await container.close()

        assert seen == [77]


class TestCoreProviderLifecycle:

    @pytest.mark.asyncio
    async def test_when_container_closed_expect_pool_stopped_before_driver(
        self,
    ):
        call_order: list[str] = []
        driver = MagicMock()
        driver.stop.side_effect = lambda: call_order.append("driver")
        session_pool = MagicMock()
        session_pool.stop.side_effect = lambda: call_order.append("pool")

        with patch(f"{CORE_PROVIDER}.create_ydb_driver", return_value = driver), \
            patch(f"{CORE_PROVIDER}.ydb.SessionPool", return_value = session_pool):
            container = create_container(FakeIdentityProvider())
            await container.get(REAL_SESSION_POOL)
            await container.close()

        assert call_order == ["pool", "driver"]


class FakeIdentityProvider(Provider):
    """Только I18nContext: YDB остаётся настоящим провайдером с подменёнными фабриками."""

    @provide(scope = Scope.REQUEST)
    def get_i18n_context(self) -> I18nContext:
        return _fake_i18n_context()


class TestStandaloneI18nProvider:

    @pytest.mark.asyncio
    async def test_when_standalone_expect_strings_with_default_locale(self):
        container = make_async_container(StandaloneI18nProvider(), _StringsOnlyProvider())

        async with container() as request_container:
            actual = await request_container.get(Strings)

        await container.close()
        assert actual.locale == "ru"


class _StringsOnlyProvider(Provider):

    @provide(scope = Scope.REQUEST)
    def get_strings(self, i18n: I18nContext) -> Strings:
        return Strings(i18n = i18n)
