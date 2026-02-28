import asyncio
import datetime
import ydb
from ydb import Driver, Session

from bot.domain.const.env_const import DEBUG_MODE, DEBUG_MODE_DATABASE
from bot.domain.model.SaveMessageModel import SaveMessageModel


# TODO abstract
# TODO data sources
class ChatHistoryRepositoryImpl:

    def __init__(
        self,
        ydb_session_pool: ydb.SessionPool,
        driver: Driver,
    ):
        self.pool = ydb_session_pool
        self.table_name = "chat_events_debug" if DEBUG_MODE_DATABASE else "chat_events_release"
        self.driver = driver

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
                commit_tx = True,
            )
            return [row for row in result_sets[0].rows]

        # Используем именованный аргумент callee для retry_operation_sync
        messages = await asyncio.to_thread(
            self.pool.retry_operation_sync,
            callee = execute,
        )

        return messages

    async def add_text_message_list(
        self,
        message_list: list[SaveMessageModel],
    ) -> None:
        if not message_list:
            return  # ничего не делаем, если список пуст

        rows = []
        for msg in message_list:
            row = {
                'chat_id': int(msg.chat_id),
                'created_at': datetime.datetime.now(),
                # метка времени для каждого сообщения
                'message_id': int(msg.message_id),
                'role': str(msg.role),
                'content': str(msg.content),
                'event_type': 'text',
                'reply_to_id': msg.reply_to_id,  # может быть None
                'text_quote': msg.text_quote,  # может быть None
                'business_conn_id': str(
                    msg.business_connection_id,
                ) if msg.business_connection_id else None,
            }
            rows.append(row)

        def bulk():
            column_types = ydb.BulkUpsertColumns()
            column_types.add_column('chat_id', ydb.PrimitiveType.Uint64)
            column_types.add_column('created_at', ydb.PrimitiveType.Timestamp)
            column_types.add_column('message_id', ydb.PrimitiveType.Uint64)
            column_types.add_column('role', ydb.PrimitiveType.Utf8)
            column_types.add_column('content', ydb.PrimitiveType.Utf8)
            column_types.add_column('event_type', ydb.PrimitiveType.Utf8)
            column_types.add_column(
                'reply_to_id', ydb.OptionalType(ydb.PrimitiveType.Uint64),
            )
            column_types.add_column(
                'text_quote', ydb.OptionalType(ydb.PrimitiveType.Utf8),
            )
            column_types.add_column(
                'business_conn_id', ydb.OptionalType(ydb.PrimitiveType.Utf8),
            )

            self.pool.retry_operation_sync(
                callee = self.driver.table_client.bulk_upsert(
                    table_path = self.table_name,
                    rows = rows,
                    column_types = column_types,
                ),
            )

        # Запускаем bulk_upsert в отдельном потоке, так как это блокирующая операция
        await asyncio.to_thread(
            bulk,
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
            callee = execute,
        )
        print(f"SUCCESS: Cleared history for chat {chat_id}")
