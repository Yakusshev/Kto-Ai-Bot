from typing import Callable, Dict, Any, Awaitable

import ydb
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.core.di.DiConst import DiConst
from bot.feature.admin.domain.FormatUserChatModelListUseCase import \
    FormatUserChatModelListUseCase
from bot.feature.admin.domain.scenario.GetRemindInfoTextScenario import \
    GetRemindInfoTextScenario
from bot.feature.business.domain.usecase.GetInactiveChatListUseCase import \
    GetInactiveChatListUseCase
from bot.util.log_util import get_logger


class GetRemindInfoTextScenarioMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:

        data[DiConst.GET_REMIND_INFO_TEXT_SCENARIO] = GetRemindInfoTextScenario(
            get_inactive_chat_list_use_case = GetInactiveChatListUseCase(
                chat_history_repository = data[DiConst.CHAT_HISTORY_REPOSITORY],
                user_repository = data[DiConst.USER_REPOSITORY],
            ),
            format_user_chat_model_list_use_case = FormatUserChatModelListUseCase(),
        )

        return await handler(event, data)


logger = get_logger(GetRemindInfoTextScenarioMiddleware.__name__)