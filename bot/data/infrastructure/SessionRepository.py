import asyncio
import datetime
import ydb
from aiogram.types import Message

from bot.domain.const.env_const import DEBUG_MODE, DEBUG_MODE_DATABASE
from bot.resource.string.strings import EMPTY_MESSAGE

class SessionRepository:

    def __init__(self, ydb_session_pool: ydb.SessionPool):
        self.pool = ydb_session_pool
        self.table_name = "chat_events_debug" if DEBUG_MODE_DATABASE else "chat_events_release"

    async def get_session_data(self, chat_id: int) -> list[dict]:
        """
        Получает историю сообщений.
        Возвращает кортеж (summary, messages) для совместимости с ChatService.
        """
        query = f"""
            DECLARE $chat_id AS Uint64;
            SELECT * FROM {self.table_name} 
            WHERE chat_id = $chat_id 
            ORDER BY created_at ASC;
        """

        def execute(session):
            # Явная подготовка запроса обязательна для корректной типизации
            prepared_query = session.prepare(query)
            result_sets = session.transaction().execute(
                query = prepared_query,
                parameters = {'$chat_id': int(chat_id)},
                commit_tx = True
            )
            return [row for row in result_sets[0].rows]

        # Используем именованный аргумент callee для retry_operation_sync
        messages = await asyncio.to_thread(
            self.pool.retry_operation_sync,
            callee = execute
        )

        return messages

    async def add_text_message(
        self,
        message: Message,
        role: str,
        content: str,
    ):
        """
        Сохраняет сообщение в YDB.
        """
        reply_to_id = None
        text_quote = None

        if message.reply_to_message:
            reply_to_id = int(message.reply_to_message.message_id)
            if message.quote:
                text_quote = str(message.quote.text)

        query = f"""
            DECLARE $chat_id AS Uint64;
            DECLARE $created_at AS Timestamp;
            DECLARE $message_id AS Uint64;
            DECLARE $role AS Utf8;
            DECLARE $content AS Utf8;
            DECLARE $event_type AS Utf8;
            DECLARE $reply_to_id AS Uint64?;
            DECLARE $text_quote AS Utf8?;
            DECLARE $business_conn_id AS Utf8?;

            UPSERT INTO {self.table_name} (
                chat_id, created_at, message_id, role, content, 
                event_type, reply_to_id, text_quote, business_conn_id
            ) VALUES (
                $chat_id, $created_at, $message_id, $role, $content, 
                $event_type, $reply_to_id, $text_quote, $business_conn_id
            );
        """

        if content == "":
            content = EMPTY_MESSAGE

        # Подготовка параметров с явным приведением типов
        params = {
            '$chat_id': int(message.chat.id),
            '$created_at': datetime.datetime.now(),
            '$message_id': int(message.message_id),
            '$role': str(role),
            '$content': str(content),
            '$event_type': 'text',
            '$reply_to_id': reply_to_id,
            '$text_quote': text_quote,
            '$business_conn_id': str(message.business_connection_id) if message.business_connection_id else None
        }

        def execute(session):
            prepared_query = session.prepare(query)
            session.transaction().execute(
                query = prepared_query,
                parameters = params,
                commit_tx = True
            )

        return await asyncio.to_thread(
            self.pool.retry_operation_sync,
            callee = execute
        )

    async def clear_chat_history(self, chat_id: int):
        """
        Удаляет историю чата.
        """
        query = f"""
            DECLARE $chat_id AS Uint64;
            DELETE FROM {self.table_name} WHERE chat_id = $chat_id;
        """

        def execute(session):
            prepared_query = session.prepare(query)
            session.transaction().execute(
                query = prepared_query,
                parameters = {'$chat_id': int(chat_id)},
                commit_tx = True,
            )

        await asyncio.to_thread(
            self.pool.retry_operation_sync,
            callee = execute
        )
        print(f"SUCCESS: Cleared history for chat {chat_id}")
