from aiogram.filters import BaseFilter
from aiogram.types import Message

from bot.core.domain.const.env_const import ADMIN_ID_LIST
from bot.util.log_util import get_logger


class IsRemindCommand(BaseFilter):

    async def __call__(
        self,
        message: Message,
        **kwargs,
    ) -> bool:
        splitted = message.text.split(sep = "_")
        splitted[0]
        return message.from_user.id in ADMIN_ID_LIST

logger = get_logger(Asdasd.__name__)