from datetime import datetime
from unittest.mock import MagicMock

import pytest
import ydb
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Chat, Message, Update, User
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore
from dishka import Provider, Scope, provide
from dishka.integrations.aiogram import AiogramProvider, FromDishka, setup_dishka

from bot.core.di.AiogramI18nProvider import AiogramI18nProvider
from bot.core.di.container import create_container
from bot.feature.business.data.datasource.TelegramRemoteDataSource import \
    TelegramRemoteDataSource
from bot.feature.business.data.repository.TaskSchedulerRepositoryImpl import \
    TaskSchedulerRepositoryImpl
from bot.feature.business.domain.repository.AiRepository import AiRepository
from bot.resource.Strings import Strings


class FakeBoundariesProvider(Provider):
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


class TestAiogramIntegration:

    @pytest.mark.asyncio
    async def test_when_update_arrives_expect_handler_gets_strings_and_scheduler(self):
        received: dict[str, object] = {}
        router = Router()

        @router.message()
        async def handler(
            message: Message,
            strings: FromDishka[Strings],
            scheduler: FromDishka[TaskSchedulerRepositoryImpl],
        ):
            received["strings"] = strings
            received["scheduler"] = scheduler

        container = create_container(
            FakeBoundariesProvider(),
            AiogramProvider(),
            AiogramI18nProvider(),
        )
        dispatcher = Dispatcher()
        I18nMiddleware(
            core = FluentRuntimeCore(path = "bot/resource/locales/{locale}"),
            default_locale = "ru",
        ).setup(dispatcher = dispatcher)
        setup_dishka(
            container = container,
            router = dispatcher,
            auto_inject = True,
        )
        dispatcher.include_router(router)
        bot = Bot(token = "0:test")
        # auto_inject срабатывает на startup роутера
        await dispatcher.emit_startup(
            dispatcher = dispatcher,
            bot = bot,
        )
        update = Update(
            update_id = 1,
            message = Message(
                message_id = 1,
                date = datetime.now(),
                chat = Chat(id = 1, type = "private"),
                from_user = User(id = 1, is_bot = False, first_name = "test"),
                text = "привет",
            ),
        )

        await dispatcher.feed_update(bot = bot, update = update)
        await dispatcher.emit_shutdown(
            dispatcher = dispatcher,
            bot = bot,
        )
        await container.close()
        await bot.session.close()

        assert isinstance(received["strings"], Strings)
        assert received["scheduler"] is TaskSchedulerRepositoryImpl()
