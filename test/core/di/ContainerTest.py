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
from bot.feature.business.data.repository.TaskSchedulerRepositoryImpl import \
    TaskSchedulerRepositoryImpl
from bot.feature.business.domain.repository.AiRepository import AiRepository
from bot.feature.business.entrypoint.service.ChatService import ChatService
from bot.feature.business.entrypoint.service.ReminderService import ReminderService
from bot.resource.Strings import Strings

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
    async def test_when_two_requests_expect_same_task_scheduler(
        self,
        container: AsyncContainer,
    ):
        async with container() as first_request:
            first = await first_request.get(TaskSchedulerRepositoryImpl)
            first_reminder = await first_request.get(ReminderService)
        async with container() as second_request:
            second = await second_request.get(TaskSchedulerRepositoryImpl)

        assert first is second
        assert first is TaskSchedulerRepositoryImpl()
        assert first_reminder.task_scheduler is first


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
