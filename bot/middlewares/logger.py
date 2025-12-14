import time
import asyncio
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message
from firebase_admin import firestore

from bot.services.firebase_logger import log_to_firestore


class FirestoreLoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Мы логируем только текстовые сообщения
        if not isinstance(event, Message) or not event.text:
            return await handler(event, data)

        start_time = time.time()
        
        # Выполняем основной хендлер
        result = await handler(event, data)
        
        end_time = time.time()
        response_time = round(end_time - start_time, 2)

        log_data = {
            "user_id": event.from_user.id,
            "username": event.from_user.username,
            "text": event.text,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "response_time": response_time
        }
        
        # Запускаем логирование как фоновую задачу, не дожидаясь ее завершения
        asyncio.create_task(log_to_firestore("logs", log_data))
        
        return result
