from aiogram.filters import BaseFilter
from aiogram.types import Message

from bot.core.domain.const.env_const import ADMIN_ID_LIST
from bot.util.log_util import get_logger


class IsAdminUserFilter(BaseFilter):

    async def __call__(
        self,
        message: Message,
        **kwargs,
    ) -> bool:
        logger.info(f"IsAdminUserFilter: {message.text}; {message.from_user.id in ADMIN_ID_LIST}")
        return message.from_user.id in ADMIN_ID_LIST

logger = get_logger(IsAdminUserFilter.__name__)