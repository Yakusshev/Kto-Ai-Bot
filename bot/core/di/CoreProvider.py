import asyncio
from typing import AsyncIterator

import ydb
from aiogram_i18n import I18nContext
from dishka import Provider, Scope, provide

from bot.core.data.ydb.CreateYdbDriver import create_ydb_driver
from bot.resource.Strings import Strings
from bot.util.log_util import get_logger


class CoreProvider(Provider):
    """
    Общие зависимости всех фич: YDB (APP) и Strings (REQUEST).

    Контейнер не знает про aiogram: I18nContext для Strings поставляет
    отдельный провайдер (AiogramI18nProvider или StandaloneI18nProvider).
    """

    @provide(scope = Scope.APP)
    async def get_ydb_driver(self) -> AsyncIterator[ydb.Driver]:
        driver = create_ydb_driver()
        yield driver
        # Закрывается последним (после пула): контейнер закрывает в обратном порядке
        await asyncio.to_thread(driver.stop)
        _logger.info("YDB driver остановлен")

    @provide(scope = Scope.APP)
    async def get_ydb_session_pool(
        self,
        driver: ydb.Driver,
    ) -> AsyncIterator[ydb.SessionPool]:
        session_pool = ydb.SessionPool(driver)
        yield session_pool
        await asyncio.to_thread(session_pool.stop)
        _logger.info("YDB session pool остановлен")

    @provide(scope = Scope.REQUEST)
    def get_strings(
        self,
        i18n: I18nContext,
    ) -> Strings:
        return Strings(i18n = i18n)


_logger = get_logger(CoreProvider.__name__)
