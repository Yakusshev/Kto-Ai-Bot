from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.resource.Strings import Strings


class StringsMiddleware(BaseMiddleware):
    """
    Middleware добавляет объект Strings в data для всех хендлеров.
    Ожидает, что I18nContext уже присутствует в data под ключом 'i18n'.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Получаем I18nContext из data (добавляется стандартным I18nMiddleware)
        i18n = data.get("i18n")
        if i18n is None:
            raise RuntimeError(
                "I18nContext не найден в data. Убедитесь, что I18nMiddleware подключён до StringsMiddleware."
            )

        # Создаём экземпляр Strings и кладём его в data
        data["strings"] = Strings(i18n = i18n)

        # Передаём управление дальше
        return await handler(event, data)