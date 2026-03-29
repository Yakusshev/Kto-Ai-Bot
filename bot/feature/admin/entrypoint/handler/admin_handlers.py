import re

from aiogram import Router, Bot, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from bot.feature.admin.domain.CommandConst import CommandConst
from bot.feature.admin.domain.scenario.GetRemindInfoTextScenario import \
    GetRemindInfoTextScenario
from bot.feature.admin.entrypoint.filter.IsAdminUserFilter import IsAdminUserFilter
from bot.feature.business import user_bot_manager
from bot.feature.business.domain.usecase.GetUserListUseCase import GetUserListUseCase
from bot.feature.business.domain.usecase.UpdateUserTableFromChatHistoryUseCase import \
    UpdateUserTableFromChatHistoryUseCase
from bot.feature.business.entrypoint.service.ReminderService import ReminderService
from bot.resource.Strings import Strings
from bot.util.log_util import get_logger

logger = get_logger("admin_handler")
admin_router = Router()

@admin_router.message(Command("stop"), IsAdminUserFilter())
async def __handle_stop(
    message: Message,
    bot: Bot,
    strings: Strings,
):
    logger.info(f"Handling stop command: {message}")

    await bot.send_message(
        chat_id = message.chat.id,
        text = strings.admin_stop_command_received(),
    )

    result = await user_bot_manager.stop()

    await bot.send_message(
        chat_id = message.chat.id,
        text = strings.admin_text_bot_stop_success()
        if result else strings.admin_text_bot_stop_failure(),
    )


@admin_router.message(Command("play"), IsAdminUserFilter())
async def __handle_start(
    message: Message,
    bot: Bot,
    strings: Strings,
):
    logger.info(f"Handling start command: {message}")

    await bot.send_message(
        chat_id = message.chat.id,
        text = strings.admin_start_command_received(),
    )

    result = await user_bot_manager.start()

    await bot.send_message(
        chat_id = message.chat.id,
        text = strings.admin_text_bot_start_success()
        if result else strings.admin_text_bot_start_failure(),
    )

@admin_router.message(Command("update_users"), IsAdminUserFilter())
async def __handle_update_users(
    message: Message,
    bot: Bot,
    update_user_table_from_chat_history_use_case: UpdateUserTableFromChatHistoryUseCase,
    get_user_list_use_case: GetUserListUseCase,
):
    logger.info(f"Handling users command: {message}")

    await update_user_table_from_chat_history_use_case.invoke()

    user_info_list = await get_user_list_use_case.invoke()

    for text in user_info_list:
        await bot.send_message(
            chat_id = message.chat.id,
            text = text,
        )

@admin_router.message(Command("users"), IsAdminUserFilter())
async def __handle_users_match(
    message: Message,
    bot: Bot,
    get_user_list_use_case: GetUserListUseCase,
):
    logger.info(f"Handling users command: {message}")

    user_info_list = await get_user_list_use_case.invoke()

    for text in user_info_list:
        await bot.send_message(
            chat_id = message.chat.id,
            text = text,
        )

@admin_router.message(
    F.text.startswith("/remind"),
    IsAdminUserFilter(),
)
async def __handle_remind_match(
    message: Message,
    bot: Bot,
    get_remind_info_text_scenario: GetRemindInfoTextScenario,
    reminder_service: ReminderService,
):
    await bot.send_message(
        chat_id = message.chat.id,
        text = f"Получена команда {message.text}",
    )

    parts = message.text.split("_", maxsplit=1)

    action = next(iter(parts[1:2]), None)

    if not action:
        # Если аргументов нет, можно вернуть общий список или ошибку
        user_info_list = await get_remind_info_text_scenario.invoke()

        for text in user_info_list:
            await bot.send_message(
                chat_id = message.chat.id,
                text = text,
            )
    else:
        await reminder_service.invoke(args = action)

        await bot.send_message(
            chat_id = message.chat.id,
            text = f"Команда {message.text} обработана",
        )



@admin_router.message()
async def debug_all(message: Message):
    print(f"asdasd {message.text}")
    logger.info(f"DEBUG: Catch all in admin router: {message.text}")

