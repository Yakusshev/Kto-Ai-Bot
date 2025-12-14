import time
import asyncio
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message
from firebase_admin.firestore import SERVER_TIMESTAMP

# Импортируем новую функцию
from bot.services.firebase_logger import log_message_to_history


class FirestoreLoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Логируем только текстовые сообщения
        if not event.text:
            return await handler(event, data)

        start_time = time.time()
        
        # Выполняем основной хендлер
        result = await handler(event, data)
        
        end_time = time.time()
        response_time = round(end_time - start_time, 2)

        # Формируем данные для лога в соответствии с новой схемой
        log_data = {
            "role": "user",
            "text": event.text,
            "username": event.from_user.username,
            "timestamp": SERVER_TIMESTAMP,
            "response_time_ms": int(response_time * 1000) # Сохраняем в миллисекундах для точности
        }
        
        # Запускаем логирование как фоновую задачу
        asyncio.create_task(log_message_to_history(event.from_user.id, log_data))
        
        return result
