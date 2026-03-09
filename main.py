# main.py
import asyncio
import locale
import logging

from aiogram import Dispatcher, types
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore

from bot.feature.admin import admin_bot_manager
from bot.feature.admin.entrypoint.handler.handlers import admin_router
from bot.feature.business import user_bot_manager
from bot.feature.business.di.ChatServiceMiddleware import ChatServiceMiddleware
from bot.feature.business.di.StringsMiddleware import StringsMiddleware
from bot.feature.business.entrypoint.business_message_handlers import business_router
from bot.util.log_util import get_logging_config
import logging.config


async def main():
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

    i18n = I18nMiddleware(
        core = FluentRuntimeCore(path = "bot/resource/locales/{locale}"),
        default_locale = "ru",
    )

    i18n.setup(dispatcher = user_bot_manager.dispatcher)
    i18n.setup(dispatcher = admin_bot_manager.dispatcher)

    await start_user_dispatcher_polling_task()
    await start_admin_dispatcher_polling_task()

    await asyncio.Future()

    while True:
        # Запрашиваем ввод у пользователя
        user_input = input("Ожидание ввода\n")

        # Проверяем условие выхода (игнорируем регистр букв)
        if user_input.lower() == "exit":
            print("Программа завершена.")
            break
        else:
            # Здесь можно выполнить любые действия с введёнными данными
            print(f"Вы ввели: {user_input}")


async def start_user_dispatcher_polling_task():
    user_bot_manager.dispatcher.business_message.middleware(StringsMiddleware())

    setup_business_router()

    await user_bot_manager.start()


def setup_business_router():
    user_bot_manager.dispatcher.business_message.middleware(ChatServiceMiddleware())

    # 4. Регистрируем обработчик подключения к бизнес-аккаунту
    @user_bot_manager.dispatcher.business_connection()
    async def on_business_connection(connection: types.BusinessConnection):
        """Логирует факт подключения или отключения."""
        conn_id = connection.id
        is_enabled = connection.is_enabled
        user_id = connection.user.id

        if is_enabled:
            logging.info(
                f"User {user_id} connected business account. Connection ID: {conn_id}",
            )
        else:
            logging.warning(
                f"User {user_id} DISABLED business account. Connection ID: {conn_id}",
            )

    user_bot_manager.dispatcher.include_router(router = business_router)


async def start_admin_dispatcher_polling_task():
    admin_bot_manager.dispatcher.message.middleware(StringsMiddleware())

    admin_bot_manager.dispatcher.include_router(router = admin_router)

    await admin_bot_manager.start()


if __name__ == '__main__':

    logging.config.dictConfig(get_logging_config())

    asyncio.run(main())
