from aiogram import Router, F
from aiogram.types import Message
from dishka import FromDishka

from bot.feature.business.domain.model.ChatEvent import ChatEvent, ChatEventKind
from bot.feature.business.domain.model.ChatStep import ChatStepContext
from bot.feature.business.domain.model.SaveMessageModel import MessageRole
from bot.feature.business.domain.usecase.ProcessChatEventUseCase import \
    ProcessChatEventUseCase
from bot.feature.business.entrypoint.service.ChatService import ChatService
from bot.resource.Strings import Strings
from bot.util.log_util import get_logger

logger = get_logger("business_handler")
business_router = Router()


# ------------------------------------------------------------------ #
#  Обработчики входящих сообщений                                      #
# ------------------------------------------------------------------ #

@business_router.business_message(F.text)
async def __handle_text(
    message: Message,
    chat_service: FromDishka[ChatService],
    process_chat_event: FromDishka[ProcessChatEventUseCase],
):
    await __check_message_role(
        message = message,
        chat_service = chat_service,
        process_chat_event = process_chat_event,
        text_content = message.text,
    )


@business_router.business_message(F.sticker)
async def __handle_sticker(
    message: Message,
    chat_service: FromDishka[ChatService],
    process_chat_event: FromDishka[ProcessChatEventUseCase],
    strings: FromDishka[Strings],
):
    await __check_message_role(
        message = message,
        chat_service = chat_service,
        process_chat_event = process_chat_event,
        text_content = strings.sticker_not_loaded(emoji = message.sticker.emoji),
    )


@business_router.business_message(F.photo)
async def __handle_photo(
    message: Message,
    chat_service: FromDishka[ChatService],
    process_chat_event: FromDishka[ProcessChatEventUseCase],
    strings: FromDishka[Strings],
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
    await __check_message_role(
        message = message,
        chat_service = chat_service,
        process_chat_event = process_chat_event,
        text_content = text_content,
    )


@business_router.business_message(F.voice)
async def __handle_voice(
    message: Message,
    chat_service: FromDishka[ChatService],
    process_chat_event: FromDishka[ProcessChatEventUseCase],
    strings: FromDishka[Strings],
):
    await __check_message_role(
        message = message,
        chat_service = chat_service,
        process_chat_event = process_chat_event,
        text_content = strings.voice_message_cannot_be_loaded(),
    )


@business_router.business_message(F.video_note)
async def __handle_video_note(
    message: Message,
    chat_service: FromDishka[ChatService],
    process_chat_event: FromDishka[ProcessChatEventUseCase],
    strings: FromDishka[Strings],
):
    await __check_message_role(
        message = message,
        chat_service = chat_service,
        process_chat_event = process_chat_event,
        text_content = strings.video_message_cannot_be_loaded(),
    )


# ------------------------------------------------------------------ #
#  Центральная логика                                                  #
# ------------------------------------------------------------------ #

async def __check_message_role(
    message: Message,
    chat_service: ChatService,
    process_chat_event: ProcessChatEventUseCase,
    text_content: str,
) -> None:
    """
    Точка входа для любого типа сообщения.
    Фильтрует только сообщения, отправленные пользователем самому себе
    через business-соединение.
    """
    by_assistant = message.from_user.id != message.chat.id

    if by_assistant:
        # отправлено в ручную: отмена ответа = новый талон, шаги со старым тихо завершатся
        logger.info(
            "MESSAGE NOT_BY_USER: %s | chat_id=%s | message=%s",
            text_content, message.chat.id, message,
        )
        await process_chat_event.invoke(
            chat_id = message.chat.id,
            event = ChatEvent(
                kind = ChatEventKind.OWNER_MESSAGE,
                message_id = message.message_id,
            ),
        )
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
            chat_service = chat_service,
            process_chat_event = process_chat_event,
            text_content = text_content,
        )


async def __handle_user_message(
    message: Message,
    chat_service: ChatService,
    process_chat_event: ProcessChatEventUseCase,
    text_content: str,
):
    # Сохраняем в БД ВСЕГДА и НЕМЕДЛЕННО, до любой логики
    await chat_service.save_message(
        message = message,
        text_content = text_content,
        role = MessageRole.USER,
    )

    # Дальше ответ ведут отложенные шаги: прочитать -> печатает -> сгенерировать и отправить
    await process_chat_event.invoke(
        chat_id = message.chat.id,
        event = ChatEvent(
            kind = ChatEventKind.USER_MESSAGE,
            message_id = message.message_id,
        ),
        context = ChatStepContext(
            business_connection_id = message.business_connection_id,
            username = message.from_user.username or "",
            full_name = message.from_user.full_name,
            message_datetime = message.date,
            message_text = text_content,
            message_id = message.message_id,
        ),
    )
