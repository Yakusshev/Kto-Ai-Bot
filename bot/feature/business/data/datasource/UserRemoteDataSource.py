import asyncio
import time
from typing import Any

import ydb
from ydb import Session, SessionPool, Driver, BulkUpsertColumns

from bot.core.domain.const.env_const import DEBUG_MODE_DATABASE, YDB_PATH
from bot.feature.business.domain.model.UserModel import UserModel
from bot.util.log_util import get_logger


class Column:
    ID = "id"
    USERNAME = "username"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    BIO = "bio"
    BIRTHDATE = "birthdate"
    BUSINESS_CONNECTION_ID = "business_connection_id"
    UPDATE_DATE = "update_date" #Последнее время обновления информации о пользователе
    CHANNEL_TITLE = "channel_title"
    CHANNEL_USERNAME = "channel_username"
    CHANNEL_ID = "channel_id"


class UserRemoteDataSource:
    TABLE_NAME_DEBUG = "users_debug"
    TABLE_NAME_RELEASE = "users_release"

    def __init__(
        self,
        ydb_session_pool: SessionPool,
        driver: Driver,
    ):
        self.ydb_session_pool = ydb_session_pool
        self.table_name = UserRemoteDataSource.TABLE_NAME_DEBUG \
            if DEBUG_MODE_DATABASE \
            else UserRemoteDataSource.TABLE_NAME_RELEASE
        self.driver = driver
        self.column_types = self.create_column_types()

    async def create_table(self):
        query = f"""
            CREATE TABLE IF NOT EXISTS users (
                {Column.ID} Int64 NOT NULL,
                {Column.USERNAME} Utf8?,
                {Column.FIRST_NAME} Utf8 NOT NULL,
                {Column.LAST_NAME} Utf8?,
                {Column.BIO} Utf8?,
                {Column.BIRTHDATE} Timestamp?,
                {Column.BUSINESS_CONNECTION_ID} Utf8?,
                {Column.UPDATE_DATE} Timestamp,
                {Column.CHANNEL_TITLE} Utf8?,
                {Column.CHANNEL_USERNAME} Utf8?,
                {Column.CHANNEL_ID} Int64?,
                PRIMARY KEY (id)
            );
        """

        def execute(session: Session) -> Any:
            return session.transaction().execute(
                query = session.prepare(query),
                commit_tx = True,
            )

        result = await asyncio.to_thread(
            self.ydb_session_pool.retry_operation_sync,
            callee = execute,
        )
        print(result)

    async def add_users(
        self,
        user_model_list: list[UserModel],
    ):
        user_rows = []

        for user_model in user_model_list:
            user_rows.append(
                {
                    Column.ID: user_model.id,
                    Column.USERNAME: user_model.username,
                    Column.FIRST_NAME: user_model.first_name,
                    Column.LAST_NAME: user_model.last_name,
                    Column.BUSINESS_CONNECTION_ID: user_model.business_connection_id,
                },
            )

        await self.bulk_upsert_with_retries(rows = user_rows)

    async def bulk_upsert_with_retries(
        self,
        rows: list,
    ):
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

    async def get_user_tuple(self) -> tuple[UserModel, ...]:
        query = f"""
            SELECT * FROM {self.table_name};
        """

        def execute(session) -> list[dict]:
            prepared_query = session.prepare(query)
            result_sets = session.transaction().execute(
                query = prepared_query,
                parameters = {},
                commit_tx = True,
            )
            rows = result_sets[0].rows
            return [dict(row) for row in rows]

        users_response = await asyncio.to_thread(
            self.ydb_session_pool.retry_operation_sync,
            callee = execute,
        )

        _logger.debug(f"get_user_tuple: users_response = {users_response}")

        rows = users_response[0].rows

        user_model_list = []
        for row in rows:
            user_model_list.append(
                UserModel(
                    id = row[Column.ID],
                    first_name = row[Column.FIRST_NAME],
                    last_name = row[Column.LAST_NAME],
                    username = row[Column.USERNAME],
                    business_connection_id = row[Column.BUSINESS_CONNECTION_ID],
                )
            )

        return tuple(user_model_list)


    @staticmethod
    def create_column_types() -> BulkUpsertColumns:
        column_types = ydb.BulkUpsertColumns()

        column_types.add_column(Column.ID, ydb.PrimitiveType.Uint64)
        column_types.add_column(Column.USERNAME, ydb.PrimitiveType.Utf8)
        column_types.add_column(Column.FIRST_NAME, ydb.PrimitiveType.Utf8)
        column_types.add_column(Column.LAST_NAME, ydb.PrimitiveType.Utf8)
        column_types.add_column(Column.BUSINESS_CONNECTION_ID, ydb.PrimitiveType.Utf8)

        return column_types

    def get_table_path(self) -> str:
        return f"{YDB_PATH}/{self.table_name}"


_logger = get_logger(UserRemoteDataSource.__name__)