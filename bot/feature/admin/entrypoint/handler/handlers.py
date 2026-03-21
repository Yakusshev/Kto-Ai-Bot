from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message

from bot.feature.admin.entrypoint.filter.IsAdminUserFilter import IsAdminUserFilter
from bot.feature.business import user_bot_manager
from bot.feature.business.domain.usecase.GetChatInfoTupleUseCase import \
    GetChatInfoTupleUseCase
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

@admin_router.message(Command("users"), IsAdminUserFilter())
async def __handle_start(
    message: Message,
    bot: Bot,
    get_chat_info_tuple_use_case: GetChatInfoTupleUseCase,
):
    logger.info(f"Handling users command: {message}")

    try:
        result = await get_chat_info_tuple_use_case.invoke()
    except Exception as e:
        raise e
        logger.error(e)
        result = str(e)

    await bot.send_message(
        chat_id = message.chat.id,
        text = result,
    )
