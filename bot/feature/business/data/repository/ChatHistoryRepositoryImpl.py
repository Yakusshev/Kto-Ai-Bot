import asyncio
import datetime
import json
import logging
import time
from dataclasses import dataclass
from typing import cast, Any, Tuple

import ydb
from aiogram.enums import MessageOriginType
from beartype import beartype
from ydb import Driver, SessionPool, Session, BulkUpsertColumns
from ydb.convert import ResultSets, ResultSet

from bot.core.domain.const.env_const import DEBUG_MODE_DATABASE, YDB_PATH
from bot.feature.business.data.ForwardOriginRequest import \
    ForwardOriginRequest
from bot.feature.business.domain.model.ChatInfoModel import ChatInfoModel
from bot.feature.business.domain.model.SaveMessageModel import SaveMessageModel, \
    MessageRole
from bot.feature.business.domain.model.ForwardOriginState import (
    ForwardOriginState,
    ForwardOriginUserModel,
    ForwardOriginHiddenUserModel,
    ForwardOriginChatModel,
    ForwardOriginChannelModel,
)
from bot.util.log_util import get_logger


# TODO декомпозировать на датасорсы


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
    # ForwardOrigin columns
    FORWARD_ORIGIN_TYPE = "forward_origin_type"
    FORWARD_ORIGIN_DATE = "forward_origin_date"
    FORWARD_ORIGIN_JSON = "FORWARD_ORIGIN_JSON"


def _serialize_forward_origin(
    origin: ForwardOriginState | None,
) -> ForwardOriginRequest:
    """
    Сериализует ForwardOriginState в три колонки:
      - forward_origin_type  (str | None)
      - forward_origin_date  (datetime | None)
      - forward_origin_json  (str | None)  — subtype-specific поля в JSON
    """
    if origin is None:
        return ForwardOriginRequest.empty()

    origin_date = origin.date

    if isinstance(origin, ForwardOriginUserModel):
        origin = cast(ForwardOriginUserModel, origin)

        return ForwardOriginRequest(
            state = MessageOriginType.USER,
            datetime = origin_date,
            json = json.dumps(
                {
                    "id": origin.id,
                    "bot": origin.bot,
                    "username": origin.username,
                    "full_name": origin.full_name,
                },
            ),
        )
    elif isinstance(origin, ForwardOriginHiddenUserModel):
        origin = cast(ForwardOriginHiddenUserModel, origin)
        return ForwardOriginRequest(
            state = MessageOriginType.HIDDEN_USER,
            datetime = origin_date,
            json = json.dumps({"username": origin.full_name}),
        )
    elif isinstance(origin, ForwardOriginChatModel):
        return ForwardOriginRequest(
            state = MessageOriginType.CHAT,
            datetime = origin_date,
            json = json.dumps(
                {
                    "id": origin.id,
                    "title": origin.title,
                    "username": origin.username,
                },
            ),
        )
    elif isinstance(origin, ForwardOriginChannelModel):
        origin = cast(ForwardOriginChannelModel, origin)
        return ForwardOriginRequest(
            state = MessageOriginType.CHANNEL,
            datetime = origin_date,
            json = json.dumps(
                {
                    "id": origin.id,
                    "title": origin.title,
                    "username": origin.username,
                    "message_id": origin.message_id,
                },
            ),
        )
    else:
        # Неизвестный подтип — сохраняем только дату
        return ForwardOriginRequest.empty()


def _deserialize_forward_origin(
    origin_type: str | None,
    origin_date_micros: int | None,
    origin_json: str | None,
) -> ForwardOriginState | None:
    """
    Десериализует три колонки обратно в ForwardOriginState.
    """
    if origin_type is None or origin_date_micros is None:
        return None

    date = datetime.datetime.fromtimestamp(
        origin_date_micros / 1_000_000,
        tz = datetime.timezone.utc,
    )
    data: dict = json.loads(origin_json or "{}")

    try:
        if origin_type == MessageOriginType.USER:
            return ForwardOriginUserModel(
                date = date,
                id = data["id"],
                bot = data["bot"],
                username = data["username"],
                full_name = data["full_name"],
            )
        elif origin_type == MessageOriginType.HIDDEN_USER:
            return ForwardOriginHiddenUserModel(
                date = date,
                full_name = data["username"],
            )
        elif origin_type == MessageOriginType.CHAT:
            return ForwardOriginChatModel(
                date = date,
                id = data["id"],
                title = data["title"],
                username = data["username"],
            )
        elif origin_type == MessageOriginType.CHANNEL:
            return ForwardOriginChannelModel(
                date = date,
                id = data["id"],
                title = data["title"],
                username = data["username"],
                message_id = data["message_id"],
            )
        else:
            return None
    except Exception as e:
        _logger.error(f"_deserialize_forward_origin: exception {e}")
        return None


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
        self.column_types = self.create_column_types()

    async def get_session_data(self, chat_id: int) -> tuple[SaveMessageModel, ...]:
        query = f"""
            DECLARE $chat_id AS Uint64;
            SELECT * FROM {self.table_name}
            WHERE {Column.CHAT_ID} = $chat_id
            ORDER BY {Column.CREATED_AT} ASC;
        """

        def execute(session: Session) -> tuple[SaveMessageModel, ...]:
            prepared_query = session.prepare(query)
            result_sets: list[ResultSet] = session.transaction().execute(
                query = prepared_query,
                parameters = {'$chat_id': int(chat_id)},
                commit_tx = True,
            )
            rows: list[dict[str, Any]] = result_sets[0].rows
            models = []
            for row in rows:
                timestamp_micros = row[Column.CREATED_AT]

                forward_origin = _deserialize_forward_origin(
                    origin_type = row.get(Column.FORWARD_ORIGIN_TYPE),
                    origin_date_micros = row.get(Column.FORWARD_ORIGIN_DATE),
                    origin_json = row.get(Column.FORWARD_ORIGIN_JSON),
                )

                model = SaveMessageModel(
                    chat_id = row[Column.CHAT_ID],
                    created_at = datetime.datetime.fromtimestamp(
                        timestamp = timestamp_micros / 1_000_000,
                        tz = datetime.timezone.utc,
                    ),
                    message_id = row[Column.MESSAGE_ID],
                    role = MessageRole.ASSISTANT
                    if row[Column.ROLE] == MessageRole.ASSISTANT.value
                    else MessageRole.USER,
                    content = row[Column.CONTENT],
                    event_type = row[Column.EVENT_TYPE],
                    reply_to_id = row.get(Column.REPLY_TO_ID),
                    text_quote = row.get(Column.TEXT_QUOTE),
                    business_connection_id = row.get(Column.BUSINESS_CONN_ID),
                    forward_origin = forward_origin,
                )
                models.append(model)
            return tuple(models)

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
            _logger.error("add_text_message_list: message_list is empty")
            return

        rows = []
        for msg in message_list:
            origin_request = _serialize_forward_origin(
                msg.forward_origin,
            )

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
                    Column.FORWARD_ORIGIN_TYPE: origin_request.state,
                    Column.FORWARD_ORIGIN_DATE: origin_request.datetime,
                    Column.FORWARD_ORIGIN_JSON: origin_request.json,
                },
            )

        def bulk():
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    self.driver.table_client.bulk_upsert(
                        table_path = self.get_table_path(),
                        rows = rows,
                        column_types = self.column_types,
                    )
                    return
                except Exception as e:
                    _logger.error(e)
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(1 * (attempt + 1))

        await asyncio.to_thread(bulk)

    @staticmethod
    def create_column_types() -> BulkUpsertColumns:
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
        column_types.add_column(
            Column.FORWARD_ORIGIN_TYPE, ydb.OptionalType(ydb.PrimitiveType.Utf8),
        )
        column_types.add_column(
            Column.FORWARD_ORIGIN_DATE,
            ydb.OptionalType(ydb.PrimitiveType.Timestamp),
        )
        column_types.add_column(
            Column.FORWARD_ORIGIN_JSON, ydb.OptionalType(ydb.PrimitiveType.Json),
        )

        return column_types

    async def get_chat_info_tuple(self) -> Tuple[ChatInfoModel, ...]:
        query = f"""
            SELECT 
                {Column.CHAT_ID},
                {Column.BUSINESS_CONN_ID},
                msg_count AS {ChatInfo.MESSAGE_COUNT},
                created_at AS {ChatInfo.LAST_MESSAGE_DATE},
                role AS {ChatInfo.LAST_MESSAGE_ROLE},
                content AS {ChatInfo.LAST_MESSAGE_CONTENT}
            FROM (
                SELECT 
                    {Column.CHAT_ID},
                    {Column.BUSINESS_CONN_ID},
                    {Column.ROLE},
                    {Column.CONTENT},
                    {Column.CREATED_AT},
                    COUNT(*) OVER (PARTITION BY {Column.CHAT_ID}) AS msg_count,
                    ROW_NUMBER() OVER (PARTITION BY {Column.CHAT_ID} ORDER BY {Column.CREATED_AT} DESC) AS rn
                FROM {ChatHistoryConst.TABLE_NAME_RELEASE}
            )
            WHERE rn = 1
            ORDER BY {ChatInfo.MESSAGE_COUNT} DESC;
        """

        def execute(session: Session) -> list[ResultSet]:
            prepared_query = session.prepare(query)
            result_sets = session.transaction().execute(
                query = prepared_query,
                commit_tx = True,
            )
            return result_sets

        result_set: list[ResultSet] = await asyncio.to_thread(
            self.ydb_session_pool.retry_operation_sync,
            callee = execute,
        )
        rows: list[dict[str, Any]] = result_set[0].rows

        _logger.debug(rows)

        chat_models = [self.to_chat_info_model(chat) for chat in rows]

        return tuple(chat_models)

    @staticmethod
    def to_chat_info_model(
        chat_info: dict[str, Any],
    ) -> ChatInfoModel:
        timestamp_micros = chat_info[ChatInfo.LAST_MESSAGE_DATE]

        return ChatInfoModel(
            id = chat_info[Column.CHAT_ID],
            business_connection_id = chat_info[Column.BUSINESS_CONN_ID],
            message_count = chat_info[ChatInfo.MESSAGE_COUNT],
            last_message_date = datetime.datetime.fromtimestamp(
                timestamp = timestamp_micros / 1_000_000,
                tz = datetime.timezone.utc,
            ),
            last_message_role = MessageRole.ASSISTANT
            if chat_info[ChatInfo.LAST_MESSAGE_ROLE] == MessageRole.ASSISTANT.value
            else MessageRole.USER,
            last_message_content = chat_info[ChatInfo.LAST_MESSAGE_CONTENT],
        )

    def get_table_path(self) -> str:
        return f"{YDB_PATH}/{self.table_name}"


class ChatInfo:
    MESSAGE_COUNT = "message_count"
    LAST_MESSAGE_DATE = "last_message_date"
    LAST_MESSAGE_ROLE = "last_message_role"
    LAST_MESSAGE_CONTENT = "last_message_content"


_logger = get_logger(ChatHistoryRepositoryImpl.__name__)
