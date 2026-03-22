import asyncio
import time
from typing import Any, List, Dict, Optional

import ydb
from aiogram.types import Birthdate
from ydb import Session, SessionPool, Driver, BulkUpsertColumns

from bot.core.domain.const.env_const import DEBUG_MODE_DATABASE, YDB_PATH
from bot.feature.business.domain.model.UserModel import UserModel, BirthdateModel
from bot.feature.business.domain.util.datetime_util import moscow_datetime
from bot.util.log_util import get_logger


class Column:
    ID = "id"
    USERNAME = "username"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    BIO = "bio"
    BIRTHDATE = "birthdate"
    BUSINESS_CONNECTION_ID = "business_connection_id"
    UPDATE_DATE = "update_date"
    CHANNEL_TITLE = "channel_title"
    CHANNEL_USERNAME = "channel_username"
    CHANNEL_ID = "channel_id"


class UserRemoteDataSource:
    TABLE_NAME_DEBUG = "users_debug"
    TABLE_NAME_RELEASE = "users_release"

    def __init__(self, ydb_session_pool: SessionPool, driver: Driver):
        self.ydb_session_pool = ydb_session_pool
        self.table_name = self.TABLE_NAME_DEBUG if DEBUG_MODE_DATABASE else self.TABLE_NAME_RELEASE
        self.driver = driver
        self.column_types = self.create_column_types()

    async def create_table_if_not_exists(self):
        # Важно: В YDB для BulkUpsert типы в таблице должны строго соответствовать типам в BulkUpsertColumns
        query = f"""
            CREATE TABLE IF NOT EXISTS `{self.table_name}` (
                {Column.ID} Int64,
                {Column.USERNAME} Utf8,
                {Column.FIRST_NAME} Utf8,
                {Column.LAST_NAME} Utf8,
                {Column.BIO} Utf8,
                {Column.BIRTHDATE} Utf8,
                {Column.BUSINESS_CONNECTION_ID} Utf8,
                {Column.UPDATE_DATE} Timestamp,
                {Column.CHANNEL_TITLE} Utf8,
                {Column.CHANNEL_USERNAME} Utf8,
                {Column.CHANNEL_ID} Int64,
                PRIMARY KEY ({Column.ID})
            );
        """

        def execute(session: Session) -> Any:
            return session.execute_scheme(query)

        await asyncio.to_thread(
            self.ydb_session_pool.retry_operation_sync,
            callee = execute,
        )

    async def add_users(self, user_model_list: List[UserModel]):
        user_rows = []


        for user in user_model_list:
            user_rows.append(
                {
                    Column.ID: user.id,
                    Column.USERNAME: user.username,
                    Column.FIRST_NAME: user.first_name,
                    Column.LAST_NAME: user.last_name,
                    Column.BIO: user.bio,
                    Column.BIRTHDATE: self.birthdate_to_str(user.birthdate),
                    Column.BUSINESS_CONNECTION_ID: user.business_connection_id,
                    Column.UPDATE_DATE: user.update_date,
                    Column.CHANNEL_TITLE: user.channel_title,
                    Column.CHANNEL_USERNAME: user.channel_username,
                    Column.CHANNEL_ID: user.channel_id,
                },
            )

        await self.bulk_upsert_with_retries(rows = user_rows)

    async def bulk_upsert_with_retries(self, rows: list):
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
                    _logger.error(f"Bulk upsert failed: {e}")
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(1 * (attempt + 1))

        await asyncio.to_thread(bulk)

    async def get_user_tuple(self) -> tuple[UserModel, ...]:
        query = f"SELECT * FROM `{self.table_name}`;"

        def execute(session: Session):
            # Используем transaction().execute для SELECT
            result_sets = session.transaction().execute(
                query,
                commit_tx = True,
            )
            return result_sets[0].rows

        rows = await asyncio.to_thread(
            self.ydb_session_pool.retry_operation_sync,
            callee = execute,
        )

        user_model_list = []
        for row in rows:
            user_model_list.append(
                UserModel(
                    id = row.get(Column.ID),
                    username = row.get(Column.USERNAME),
                    first_name = row.get(Column.FIRST_NAME),
                    last_name = row.get(Column.LAST_NAME),
                    bio = row.get(Column.BIO),
                    birthdate = self.str_to_birthdate(row[Column.BIRTHDATE]),
                    business_connection_id = row.get(Column.BUSINESS_CONNECTION_ID),
                    update_date = moscow_datetime(micros = row[Column.UPDATE_DATE]),
                    channel_title = row.get(Column.CHANNEL_TITLE),
                    channel_username = row.get(Column.CHANNEL_USERNAME),
                    channel_id = row.get(Column.CHANNEL_ID),
                ),
            )

        return tuple(user_model_list)

    @staticmethod
    def create_column_types() -> BulkUpsertColumns:
        column_types = ydb.BulkUpsertColumns()

        # Для опциональных полей (NULL) используем Optional
        column_types.add_column(Column.ID, ydb.PrimitiveType.Int64)
        column_types.add_column(
            Column.USERNAME, ydb.OptionalType(ydb.PrimitiveType.Utf8),
        )
        column_types.add_column(Column.FIRST_NAME, ydb.PrimitiveType.Utf8)
        column_types.add_column(
            Column.LAST_NAME, ydb.OptionalType(ydb.PrimitiveType.Utf8),
        )
        column_types.add_column(Column.BIO, ydb.OptionalType(ydb.PrimitiveType.Utf8))
        column_types.add_column(
            Column.BIRTHDATE, ydb.OptionalType(ydb.PrimitiveType.Utf8),
        )
        column_types.add_column(
            Column.BUSINESS_CONNECTION_ID, ydb.OptionalType(ydb.PrimitiveType.Utf8),
        )
        column_types.add_column(
            Column.UPDATE_DATE, ydb.OptionalType(ydb.PrimitiveType.Timestamp),
        )
        column_types.add_column(
            Column.CHANNEL_TITLE, ydb.OptionalType(ydb.PrimitiveType.Utf8),
        )
        column_types.add_column(
            Column.CHANNEL_USERNAME, ydb.OptionalType(ydb.PrimitiveType.Utf8),
        )
        column_types.add_column(
            Column.CHANNEL_ID, ydb.OptionalType(ydb.PrimitiveType.Int64),
        )

        return column_types

    def get_table_path(self) -> str:
        # Убедитесь, что YDB_PATH не заканчивается на '/', иначе будет двойной слэш
        return f"{YDB_PATH.rstrip('/')}/{self.table_name}"

    @staticmethod
    def birthdate_to_str(birthdate: BirthdateModel | None) -> str | None:
        if birthdate and birthdate.year:
            return f"{birthdate.day}.{birthdate.month}.{birthdate.year}"
        elif birthdate:
            return f"{birthdate.day}.{birthdate.month}"
        else:
            return None

    @staticmethod
    def str_to_birthdate(birthdate: str | None) -> BirthdateModel | None:

        if not birthdate: return None

        parts = birthdate.strip().split('.')

        if len(parts) == 2:
            # Формат: DD.MM
            day, month = parts
            return BirthdateModel(
                day = int(day),
                month = int(month),
                year = None
            )
        elif len(parts) == 3:
            # Формат: DD.MM.YYYY
            day, month, year = parts

            if year:
                year = int(year)
            else:
                year = None
            return BirthdateModel(
                day = int(day),
                month = int(month),
                year = year,
            )
        else:
            _logger.info(
                f"Некорректный формат даты: '{birthdate}'. "
                f"Ожидаются форматы DD.MM или DD.MM.YYYY"
            )
            return None


_logger = get_logger(UserRemoteDataSource.__name__)
