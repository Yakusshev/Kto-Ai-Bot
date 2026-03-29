import asyncio
import datetime
import logging
import random
from asyncio import Event, Task

from aiogram import Router, F, Bot
from aiogram.types import Message

from bot.feature.business.data.repository.TaskSchedulerRepositoryImpl import \
    TaskSchedulerRepositoryImpl
from bot.feature.business.entrypoint.HumanWaitingBehavior import (
    wait_to_start_typing,
    wait_to_write_message,
)
from bot.feature.business.entrypoint.service.ChatService import ChatService
from bot.resource.Strings import Strings
from bot.feature.business.domain.model.SaveMessageModel import MessageRole
from bot.util.log_util import get_logger

logger = get_logger("business_handler")
business_router = Router()


# ------------------------------------------------------------------ #
#  Обработчики входящих сообщений                                      #
# ------------------------------------------------------------------ #

@business_router.business_message(F.text)
async def __handle_text(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
):
    await __check_message_role(
        message = message,
        bot = bot,
        chat_service = chat_service,
        text_content = message.text,
    )


@business_router.business_message(F.sticker)
async def __handle_sticker(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    strings: Strings,
):
    await __check_message_role(
        message = message,
        bot = bot,
        chat_service = chat_service,
        text_content = strings.sticker_not_loaded(emoji = message.sticker.emoji),
    )


@business_router.business_message(F.photo)
async def __handle_photo(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    strings: Strings,
):
    has_many = len(message.photo) > 1
    has_text = message.caption is not None

    if has_many and has_text:
        text_content = strings.photo_list_cannot_be_loaded_text(
            photo_number = len(message.photo),
            text = message.caption,
        )
    elif has_many:
        text_content = strings.photo_list_cannot_be_loaded(
            photo_number = len(message.photo),
        )
    elif has_text:
        text_content = strings.photo_cannot_be_loaded_text(
            text = message.caption,
        )
    else:
        text_content = strings.photo_cannot_be_loaded()
    await __check_message_role(message, bot, chat_service, text_content)


@business_router.business_message(F.voice)
async def __handle_voice(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    strings: Strings,
):
    await __check_message_role(
        message = message,
        bot = bot,
        chat_service = chat_service,
        text_content = strings.voice_message_cannot_be_loaded(),
    )


@business_router.business_message(F.video_note)
async def __handle_video_note(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    strings: Strings,
):
    await __check_message_role(
        message = message,
        bot = bot,
        chat_service = chat_service,
        text_content = strings.video_message_cannot_be_loaded(),
    )


# ------------------------------------------------------------------ #
#  Центральная логика                                                  #
# ------------------------------------------------------------------ #

async def __check_message_role(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    text_content: str,
) -> None:
    """
    Точка входа для любого типа сообщения.
    Фильтрует только сообщения, отправленные пользователем самому себе
    через business-соединение.
    """
    by_assistant = message.from_user.id != message.chat.id

    if by_assistant:
        # отправлено в ручную
        logger.info(
            "MESSAGE NOT_BY_USER: %s | chat_id=%s | message=%s",
            text_content, message.chat.id, message,
        )
        scheduler = TaskSchedulerRepositoryImpl()
        await scheduler.cancel_task(key = str(message.chat.id))
        await chat_service.save_message(
            message = message,
            text_content = text_content,
            role = MessageRole.ASSISTANT,
        )
    elif not message.business_connection_id:
        logger.warning(
            "MESSAGE NOT business_connection_id: %s | chat_id=%s | message=%s",
            text_content, message.chat.id, message,
        )
    else:
        logger.info(
            "message: %s | chat_id=%s | message=%s", text_content,
            message.chat.id, message,
        )
        await __handle_user_message(
            message = message,
            bot = bot,
            chat_service = chat_service,
            text_content = text_content,
        )


async def __handle_user_message(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    text_content: str,
):
    scheduler = TaskSchedulerRepositoryImpl()
    task_key = str(message.chat.id)

    connection_id = message.business_connection_id
    connection = await bot.get_business_connection(connection_id)

    logger.debug(f'__handle_user_message: connection = {connection}')


    try:
        await scheduler.on_message(
            key = task_key,
            # Сохранить в БД — выполнится немедленно внутри on_message
            save_coro = chat_service.save_message(
                message = message,
                text_content = text_content,
                role = MessageRole.USER,
            ),
            # Фабрика ответа — вызывается только когда пришло время отвечать
            answer_factory = lambda: __answer_message(
                bot = bot,
                chat_service = chat_service,
                text_content = text_content,
                message = message,
            ),
            # Фабрика «прочитать сообщение» — вызывается перед ответом
            read_message_factory = lambda: bot.read_business_message(
                business_connection_id = message.business_connection_id,
                chat_id = message.chat.id,
                message_id = message.message_id,
            ),
        )
    except asyncio.CancelledError:
        logger.info(
            "handle_message отменён: chat_id=%s text=%s", message.chat.id,
            text_content,
        )
        raise


async def __answer_message(
    bot: Bot,
    chat_service: ChatService,
    message: Message,
    text_content: str,
) -> None:
    """
    Генерирует и отправляет ответ нейросети.
    Показывает typing-индикатор всё время генерации.
    """
    stop_typing = asyncio.Event()
    typing_task = None
    answer_message_list: list[Message] = []

    message_chat_id = message.chat.id
    business_connection_id = message.business_connection_id

    try:
        await wait_to_start_typing(message = text_content)

        stop_typing = asyncio.Event()
        typing_task = asyncio.create_task(
            __typing_loop(
                bot = bot,
                chat_id = message_chat_id,
                business_connection_id = business_connection_id,
                stop_event = stop_typing,
            ),
        )

        ai_answer_list = await chat_service.generate_ai_response(
            message = message,
            business_connection = await bot.get_business_connection(
                business_connection_id = business_connection_id,
            ),
        )

        for ai_answer in ai_answer_list:
            await wait_to_write_message(ai_answer)

            try:
                if ai_answer:
                    sent = await bot.send_message(
                        chat_id = message_chat_id,
                        text = ai_answer,
                        business_connection_id = business_connection_id,
                    )
                    answer_message_list.append(sent)
            except Exception as e:
                logger.error(
                    f"send_message EXCEPTION\n"
                    f"message.message_id = {message.message_id}\n"
                    f"username = {message.from_user.username}\n"
                    f"fullname = {message.from_user.first_name} {message.from_user.last_name}\n"
                    f"e = {e}",
                )
            except asyncio.CancelledError as canceled_error:
                raise canceled_error

    except asyncio.CancelledError:
        await complete_answer(
            answer_message_list = answer_message_list,
            chat_service = chat_service,
            stop_typing = stop_typing,
            typing_task = typing_task,
        )
        logger.info("__answer_message отменён: chat_id=%s", message_chat_id)
        raise

    finally:
        await complete_answer(
            answer_message_list = answer_message_list,
            chat_service = chat_service,
            stop_typing = stop_typing,
            typing_task = typing_task,
        )


async def complete_answer(
    answer_message_list: list[Message],
    chat_service: ChatService,
    stop_typing: Event,
    typing_task: Task[None] | None,
):
    if stop_typing:
        stop_typing.set()
    if typing_task:
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass
    # Сохраняем отправленные сообщения бота в БД (fire-and-forget)
    if answer_message_list:
        await chat_service.save_assistant_text_message_list(
            message_list = answer_message_list,
        ),


async def __typing_loop(
    bot: Bot,
    chat_id: int,
    business_connection_id: str,
    stop_event: asyncio.Event,
) -> None:
    """
    Поддерживает статус «печатает...» пока не выставлен stop_event.
    Иногда делает паузу 1-3 сек (имитирует «задумался»).
    """

    default_pause = 7

    start_typing_time = datetime.datetime.now()

    while not stop_event.is_set():

        delta = datetime.datetime.now() - start_typing_time

        if delta.seconds > random.uniform(15, 20):
            break

        try:
            await bot.send_chat_action(
                chat_id = chat_id,
                action = "typing",
                business_connection_id = business_connection_id,
            )
        except Exception as e:
            logger.warning("typing_loop ошибка send_chat_action: %s", e)

        await asyncio.sleep(default_pause + random.uniform(1, 5))
