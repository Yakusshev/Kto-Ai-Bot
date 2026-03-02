import logging

from aiogram.filters import BaseFilter
from aiogram.types import Message

from bot.core.domain.const.env_const import ADMIN_ID_LIST


class IsAdminUserFilter(BaseFilter):

    async def __call__(
        self,
        message: Message,
        **kwargs,
    ) -> bool:
        return message.from_user.id in ADMIN_ID_LIST
