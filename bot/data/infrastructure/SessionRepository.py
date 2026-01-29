import asyncio
import datetime
import ydb
from aiogram.types import Message


class SessionRepository:

    def __init__(self, ydb_session_pool: ydb.SessionPool):
        # В YDB мы работаем через пул сессий
        self.pool = ydb_session_pool

    async def get_session_data(
            self,
            chat_id: int,
    ) -> list[dict]:
        """
        Получает историю сообщений для чата из YDB.
        Примечание: В текущей схеме таблицы 'summary' хранится отдельно
        или высчитывается. Пока выгружаем только историю.
        """
        query = """
            DECLARE $chat_id AS Uint64;
            SELECT * FROM chat_events 
            WHERE chat_id = $chat_id 
            ORDER BY created_at ASC;
        """

        def execute(session):
            # Выполняем запрос на чтение
            result_sets = session.transaction().execute(
                query,
                {'$chat_id': chat_id},
                commit_tx=True
            )
            # Превращаем результат в список словарей
            return [row for row in result_sets[0].rows]

        # retry_operation_sync делает код отказоустойчивым
        messages = await asyncio.to_thread(self.pool.retry_operation_sync, execute)
        return messages

    async def save_message(
            self,
            message: Message,
            role: str,
            content: str = None,
    ):
        final_content = content or message.text or message.caption or ""
        reply_to_id = None
        text_quote = None

        if message.reply_to_message:
            reply_to_id = message.reply_to_message.message_id
            if message.quote:
                text_quote = message.quote.text

        query = """
            DECLARE $chat_id AS Uint64;
            DECLARE $created_at AS Timestamp;
            DECLARE $message_id AS Uint64;
            DECLARE $role AS Utf8;
            DECLARE $content AS Utf8;
            DECLARE $event_type AS Utf8;
            DECLARE $reply_to_id AS Uint64?;
            DECLARE $text_quote AS Utf8?;
            DECLARE $business_conn_id AS Utf8?;

            UPSERT INTO chat_events (
                chat_id, created_at, message_id, role, content, 
                event_type, reply_to_id, text_quote, business_conn_id
            ) VALUES (
                $chat_id, $created_at, $message_id, $role, $content, 
                $event_type, $reply_to_id, $text_quote, $business_conn_id
            );
        """

        def execute(session):
            session.transaction().execute(
                query,
                {
                    '$chat_id': message.chat.id,
                    # ИСПРАВЛЕНО: используем стандартный datetime
                    '$created_at': datetime.datetime.now(),
                    '$message_id': message.message_id,
                    '$role': role,
                    '$content': final_content,
                    '$event_type': 'text',
                    '$reply_to_id': reply_to_id,
                    '$text_quote': text_quote,
                    '$business_conn_id': message.business_connection_id
                },
                commit_tx=True
            )

        # ИСПРАВЛЕНО: используем self.pool и запускаем в потоке, если метод асинхронный
        return await asyncio.to_thread(self.pool.retry_operation_sync, execute)

    async def clear_chat_history(self, chat_id: int):
        """
        Удаляет все сообщения пользователя.
        В YDB нет 'коллекций', удаляем через DELETE по ключу.
        """
        query = """
            DECLARE $chat_id AS Uint64;
            DELETE FROM chat_events WHERE chat_id = $chat_id;
        """

        def execute(session):
            session.transaction().execute(query, {'$chat_id': chat_id}, commit_tx=True)

        await asyncio.to_thread(self.pool.retry_operation_sync, execute)
        print(f"SUCCESS: Cleared history for chat {chat_id}")
