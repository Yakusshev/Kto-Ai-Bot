from aiogram_i18n.cores import BaseCore, FluentRuntimeCore
from typing_extensions import override

from bot.feature.business.data.repository.TaskSchedulerRepositoryImpl import \
    TaskSchedulerRepositoryImpl


class GracefulShutdownFluentRuntimeCore(FluentRuntimeCore):

    @override
    async def shutdown(self) -> None:
        await TaskSchedulerRepositoryImpl().wait_task_completion()
        self.locales.clear()
