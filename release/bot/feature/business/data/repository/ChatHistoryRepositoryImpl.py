import asyncio
import datetime
import time
import ydb
from ydb import Driver, SessionPool

from bot.core.domain.const.env_const import DEBUG_MODE_DATABASE, YDB_PATH
from bot.feature.business.domain.model.SaveMessageModel import SaveMessageModel, MessageRole


class ChatHistoryConst:
    TABLE_NAME_DEBUG = "chat_events_debug"
    TABLE_NAME_RELEASE = "chat_events_release"


class Column:
    CHAT_ID = "chat_id"
    CREATED_AT = "created_at"
    MESSAGE_ID = "message_id"
    ROLE = "role"
    CONTENT = "content"
    EVENT_TYPE = "event_type"
    REPLY_TO_ID = "reply_to_id"
    TEXT_QUOTE = "text_quote"
    BUSINESS_CONN_ID = "business_conn_id"


class ChatHistoryRepositoryImpl:

    def __init__(
        self,
        ydb_session_pool: SessionPool,
        driver: Driver,
    ):
        self.ydb_session_pool = ydb_session_pool
        self.table_name = ChatHistoryConst.TABLE_NAME_DEBUG \
            if DEBUG_MODE_DATABASE \
            else ChatHistoryConst.TABLE_NAME_RELEASE
        self.driver = driver

    async def get_session_data(self, chat_id: int) -> list[SaveMessageModel]:
        query = f"""
            DECLARE $chat_id AS Uint64;
            SELECT * FROM {self.table_name} 
            WHERE {Column.CHAT_ID} = $chat_id 
            ORDER BY {Column.CREATED_AT} ASC;
        """

        def execute(session):
            prepared_query = session.prepare(query)
            result_sets = session.transaction().execute(
                query = prepared_query,
                parameters = {'$chat_id': int(chat_id)},
                commit_tx = True,
            )
            rows = result_sets[0].rows
            models = []
            for row in rows:

                timestamp_micros = row[Column.CREATED_AT]

                model = SaveMessageModel(
                    chat_id = row[Column.CHAT_ID],
                    created_at = datetime.datetime.fromtimestamp(
                        timestamp = timestamp_micros / 1_000_000,
                        tz = datetime.timezone.utc,
                    ),
                    message_id = row[Column.MESSAGE_ID],
                    role = MessageRole.ASSISTANT \
                        if row[Column.ROLE] == MessageRole.ASSISTANT.value \
                        else MessageRole.USER,
                    content = row[Column.CONTENT],
                    event_type = row[Column.EVENT_TYPE],
                    reply_to_id = row.get(Column.REPLY_TO_ID),  # None допускается
                    text_quote = row.get(Column.TEXT_QUOTE),  # None допускается
                    business_connection_id = row.get(Column.BUSINESS_CONN_ID),
                    # маппинг с business_conn_id
                )
                models.append(model)
            return models

        messages = await asyncio.to_thread(
            self.ydb_session_pool.retry_operation_sync,
            callee = execute,
        )
        return messages

    async def add_text_message_list(
        self,
        message_list: list[SaveMessageModel],
    ) -> None:
        if not message_list:
            return

        rows = []
        for msg in message_list:
            rows.append(
                {
                    Column.CHAT_ID: int(msg.chat_id),
                    Column.CREATED_AT: datetime.datetime.now(),
                    Column.MESSAGE_ID: int(msg.message_id),
                    Column.ROLE: str(msg.role),
                    Column.CONTENT: str(msg.content),
                    Column.EVENT_TYPE: 'text',
                    Column.REPLY_TO_ID: msg.reply_to_id,
                    Column.TEXT_QUOTE: msg.text_quote,
                    Column.BUSINESS_CONN_ID: str(
                        msg.business_connection_id,
                    ) if msg.business_connection_id else None,
                },
            )

        column_types = ydb.BulkUpsertColumns()
        column_types.add_column(Column.CHAT_ID, ydb.PrimitiveType.Uint64)
        column_types.add_column(Column.CREATED_AT, ydb.PrimitiveType.Timestamp)
        column_types.add_column(Column.MESSAGE_ID, ydb.PrimitiveType.Uint64)
        column_types.add_column(Column.ROLE, ydb.PrimitiveType.Utf8)
        column_types.add_column(Column.CONTENT, ydb.PrimitiveType.Utf8)
        column_types.add_column(Column.EVENT_TYPE, ydb.PrimitiveType.Utf8)
        column_types.add_column(
            Column.REPLY_TO_ID, ydb.OptionalType(ydb.PrimitiveType.Uint64),
        )
        column_types.add_column(
            Column.TEXT_QUOTE, ydb.OptionalType(ydb.PrimitiveType.Utf8),
        )
        column_types.add_column(
            Column.BUSINESS_CONN_ID, ydb.OptionalType(ydb.PrimitiveType.Utf8),
        )

        def bulk():
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.driver.table_client.bulk_upsert(
                        table_path = self.get_table_path(),
                        rows = rows,
                        column_types = column_types,
                    )
                    return
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(1 * (attempt + 1))

        await asyncio.to_thread(bulk)

    def get_table_path(self) -> str:
        return f"{YDB_PATH}/{self.table_name}"
