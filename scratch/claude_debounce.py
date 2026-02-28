import asyncio
import logging
import random
from dataclasses import dataclass, field

from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram_i18n import I18nContext

from bot.domain.const.env_const import DEBUG_MODE
from bot.entrypoint.ChatService import ChatService
from bot.resource.Strings import Strings

business_router = Router()


# --- Состояние одного чата ---
@dataclass
class ChatDebounceState:
    messages: list[tuple[Message, str]] = field(
        default_factory = list,
    )  # (message, text_content)
    task: asyncio.Task | None = None
    message_count: int = 0  # сколько раз прерывали


# chat_id -> состояние
_chat_states: dict[int, ChatDebounceState] = {}


def _get_state(chat_id: int) -> ChatDebounceState:
    if chat_id not in _chat_states:
        _chat_states[chat_id] = ChatDebounceState()
    return _chat_states[chat_id]


# --- Typing loop (без изменений) ---
async def __typing_loop(
    bot: Bot,
    chat_id: int,
    business_connection_id: str,
    stop_event: asyncio.Event,
):
    while not stop_event.is_set():
        await bot.send_chat_action(
            chat_id = chat_id,
            action = "typing",
            business_connection_id = business_connection_id,
        )
        if random.random() < 0.25:
            await asyncio.sleep(random.uniform(1.0, 3.0))
        else:
            await asyncio.sleep(4.0)


# --- Основная логика с debounce ---
async def __debounced_respond(
    chat_id: int,
    business_connection_id: str,
    bot: Bot,
    chat_service: ChatService,
    strings: Strings,
    read_delay: float,
    extra_delay: float,
):
    """
    Ждёт read_delay + extra_delay секунд.
    Если за это время нас не отменили — отвечаем на все накопленные сообщения.
    """
    try:
        total_delay = read_delay + extra_delay
        print(
            f"[debounce] chat={chat_id} ждём {total_delay:.1f}s (read={read_delay:.1f} + extra={extra_delay:.1f})",
        )
        await asyncio.sleep(total_delay)
    except asyncio.CancelledError:
        print(
            f"[debounce] chat={chat_id} задача отменена — пришло новое сообщение",
        )
        raise  # обязательно пробрасываем

    state = _get_state(chat_id)
    collected = state.messages.copy()
    state.messages.clear()
    state.message_count = 0

    if not collected:
        return

    # Читаем все сообщения
    for msg, _ in collected:
        try:
            await bot.read_business_message(
                business_connection_id = business_connection_id,
                chat_id = chat_id,
                message_id = msg.message_id,
            )
        except Exception as e:
            print(f"[debounce] read_business_message error: {e}")

    # Собираем единый контент из всех сообщений
    combined_content = "\n".join(text for _, text in collected)

    # Запускаем typing
    stop_typing = asyncio.Event()
    typing_task = asyncio.create_task(
        __typing_loop(
            bot = bot,
            chat_id = chat_id,
            business_connection_id = business_connection_id,
            stop_event = stop_typing,
        ),
    )

    try:
        # Передаём последнее сообщение как message (для метаданных),
        # но контент — объединённый
        last_message = collected[-1][0]
        ai_answer_list = await chat_service.save_message_model(
            message = last_message,
            content = combined_content,
            strings = strings,
        )

        for ai_answer in ai_answer_list:
            if not DEBUG_MODE:
                write_time = len(ai_answer) / random.uniform(3, 10)
                await asyncio.sleep(write_time)

            answer_message = await bot.send_message(
                chat_id = chat_id,
                text = ai_answer,
                business_connection_id = business_connection_id,
            )
            await chat_service.handle_self_message(
                message_list = answer_message, strings = strings,
            )

    finally:
        stop_typing.set()
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass


async def __handle_message(
    message: Message,
    bot: Bot,
    chat_service: ChatService,
    text_content: str,
    strings: Strings,
):
    print("handle_business_message text_content =", text_content)

    if not message.business_connection_id:
        return

    chat_id = message.chat.id

    if message.from_user.id != message.chat.id:
        print(
            f"message.from_user.id[{message.from_user.id}] != message.chat.id[{message.chat.id}]",
        )
        await chat_service.handle_self_message(
            message_list = message,
            strings = strings,
        )
        return

    state = _get_state(chat_id)

    # Отменяем предыдущую задачу, если она ещё ждёт
    if state.task and not state.task.done():
        state.task.cancel()
        # Ждём завершения отмены, чтобы не было гонок
        try:
            await state.task
        except (asyncio.CancelledError, Exception):
            pass

    # Накапливаем сообщение
    state.messages.append((message, text_content))
    state.message_count += 1
    count = state.message_count  # N-е сообщение подряд

    # Задержка: время на прочтение + N секунд (растёт с каждым сообщением)
    read_delay = len(text_content.split()) / 2.5 if not DEBUG_MODE else 0.0
    extra_delay = float(count)  # 1 сек, 2 сек, 3 сек...

    print(
        f"[debounce] chat={chat_id} сообщение #{count}, накоплено {len(state.messages)} шт.",
    )

    state.task = asyncio.create_task(
        __debounced_respond(
            chat_id = chat_id,
            business_connection_id = message.business_connection_id,
            bot = bot,
            chat_service = chat_service,
            strings = strings,
            read_delay = read_delay,
            extra_delay = extra_delay,
        ),
    )


# --- Handlers (без изменений) ---

@business_router.business_message(F.text)
async def __handle_text(
    message: Message, bot: Bot,
    chat_service: ChatService, i18n: I18nContext,
):
    await __handle_message(
        message = message, bot = bot,
        chat_service = chat_service,
        text_content = message.text,
        strings = Strings(i18n = i18n),
    )


@business_router.business_message(F.sticker)
async def __handle_sticker(
    message: Message, bot: Bot,
    chat_service: ChatService, i18n: I18nContext,
):
    i18n_ = I18nContext if False else i18n  # type hint trick
    await __handle_message(
        message = message, bot = bot,
        chat_service = chat_service,
        text_content = i18n.get(
            'sticker-not-loaded',
            emoji = message.sticker.emoji,
        ),
        strings = Strings(i18n = i18n),
    )


@business_router.business_message(F.photo)
async def __handle_photo(
    message: Message, bot: Bot,
    chat_service: ChatService, i18n: I18nContext,
):
    strings = Strings(i18n = i18n)
    if len(message.photo) > 1 and message.text is not None:
        text_content = strings.photo_list_cannot_be_loaded_text(
            user = message.from_user.full_name,
            photo_number = len(message.photo), text = message.text,
        )
    elif len(message.photo) > 1:
        text_content = strings.photo_list_cannot_be_loaded(
            user = message.from_user.full_name,
            photo_number = len(message.photo),
        )
    elif message.text is not None:
        text_content = strings.photo_cannot_be_loaded_text(
            user = message.from_user.full_name, text = message.text,
        )
    else:
        text_content = strings.photo_cannot_be_loaded(
            user = message.from_user.full_name,
        )
    await __handle_message(
        message = message, bot = bot,
        chat_service = chat_service,
        text_content = text_content, strings = strings,
    )


@business_router.business_message(F.voice)
async def __handle_voice(
    message: Message, bot: Bot,
    chat_service: ChatService, i18n: I18nContext,
):
    strings = Strings(i18n = i18n)
    await __handle_message(
        message = message, bot = bot,
        chat_service = chat_service,
        text_content = strings.voice_message_cannot_be_loaded(
            user = message.from_user.full_name,
        ),
        strings = strings,
    )


@business_router.business_message(F.video_note)
async def __handle_video_note(
    message: Message, bot: Bot,
    chat_service: ChatService,
    i18n: I18nContext,
):
    strings = Strings(i18n = i18n)
    await __handle_message(
        message = message, bot = bot,
        chat_service = chat_service,
        text_content = strings.video_message_cannot_be_loaded(
            user = message.from_user.full_name,
        ),
        strings = strings,
    )


```

** Как
это
работает: **
```
Сообщение
1 → накапливаем, запускаем
задачу
с
задержкой(read_time + 1
с)
Сообщение
2 → отменяем
задачу, накапливаем, запускаем
с
задержкой(read_time + 2
с)
Сообщение
3 → отменяем
задачу, накапливаем, запускаем
с
задержкой(read_time + 3
с)
...
тишина...
→ задача
НЕ
отменена → отвечаем
на
все
3
сразу
