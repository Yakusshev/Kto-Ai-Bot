import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from ydb import Session, SessionPool

from bot.core.domain.const.env_const import DEBUG_MODE_DATABASE
from bot.feature.business.domain.model.ChatState import ChatPhase, ChatState


class Column:
    CHAT_ID = "chat_id"
    PHASE = "phase"
    VERSION = "version"
    PHASE_VERSION = "phase_version"
    PENDING_MESSAGE_IDS = "pending_message_ids"
    UPDATED_AT = "updated_at"


class ChatStateRemoteDataSource:
    """Таблица состояния диалога по чатам в YDB."""

    TABLE_NAME_DEBUG = "chat_state_debug"
    TABLE_NAME_RELEASE = "chat_state_release"

    def __init__(
        self,
        ydb_session_pool: SessionPool,
    ):
        self.ydb_session_pool = ydb_session_pool
        self.table_name = self.TABLE_NAME_DEBUG \
            if DEBUG_MODE_DATABASE else self.TABLE_NAME_RELEASE
        self._is_table_ready = False

    async def create_table_if_not_exists(self) -> None:
        if self._is_table_ready:
            return

        query = f"""
            CREATE TABLE IF NOT EXISTS `{self.table_name}` (
                {Column.CHAT_ID} Int64,
                {Column.PHASE} Utf8,
                {Column.VERSION} Int64,
                {Column.PHASE_VERSION} Int64,
                {Column.PENDING_MESSAGE_IDS} Utf8,
                {Column.UPDATED_AT} Timestamp,
                PRIMARY KEY ({Column.CHAT_ID})
            );
        """

        def execute(session: Session) -> Any:
            return session.execute_scheme(query)

        await asyncio.to_thread(
            self.ydb_session_pool.retry_operation_sync,
            callee = execute,
        )
        self._is_table_ready = True

    async def get(
        self,
        chat_id: int,
    ) -> ChatState | None:
        await self.create_table_if_not_exists()

        query = f"""
            DECLARE $chat_id AS Int64;
            SELECT * FROM `{self.table_name}` WHERE {Column.CHAT_ID} = $chat_id;
        """

        def execute(session: Session) -> list[dict[str, Any]]:
            result_sets = session.transaction().execute(
                query = session.prepare(query),
                parameters = {'$chat_id': chat_id},
                commit_tx = True,
            )
            return result_sets[0].rows

        rows = await asyncio.to_thread(
            self.ydb_session_pool.retry_operation_sync,
            callee = execute,
        )
        return self._to_model(rows[0]) if rows else None

    async def compare_and_set(
        self,
        expected_version: int,
        new_state: ChatState,
    ) -> bool:
        """
        Чтение версии и запись в одной serializable-транзакции.
        Конкурирующая транзакция даёт Aborted/PreconditionFailed: retry_operation_sync
        повторяет всю функцию, и повторное чтение уже видит новую version (-> False).
        """
        await self.create_table_if_not_exists()

        select_query = f"""
            DECLARE $chat_id AS Int64;
            SELECT {Column.VERSION} FROM `{self.table_name}`
            WHERE {Column.CHAT_ID} = $chat_id;
        """
        upsert_query = f"""
            DECLARE $chat_id AS Int64;
            DECLARE $phase AS Utf8;
            DECLARE $version AS Int64;
            DECLARE $phase_version AS Int64;
            DECLARE $pending AS Utf8;
            DECLARE $updated_at AS Timestamp;
            UPSERT INTO `{self.table_name}` (
                {Column.CHAT_ID},
                {Column.PHASE},
                {Column.VERSION},
                {Column.PHASE_VERSION},
                {Column.PENDING_MESSAGE_IDS},
                {Column.UPDATED_AT}
            ) VALUES (
                $chat_id, $phase, $version, $phase_version, $pending, $updated_at
            );
        """

        def execute(session: Session) -> bool:
            tx = session.transaction()
            rows = tx.execute(
                query = session.prepare(select_query),
                parameters = {'$chat_id': new_state.chat_id},
            )[0].rows
            stored_version = rows[0][Column.VERSION] if rows else 0

            if stored_version != expected_version:
                tx.rollback()
                return False

            tx.execute(
                query = session.prepare(upsert_query),
                parameters = {
                    '$chat_id': new_state.chat_id,
                    '$phase': new_state.phase.value,
                    '$version': new_state.version,
                    '$phase_version': new_state.phase_version,
                    '$pending': json.dumps(list(new_state.pending_message_ids)),
                    '$updated_at': int(new_state.updated_at.timestamp() * 1_000_000),
                },
                commit_tx = True,
            )
            return True

        return await asyncio.to_thread(
            self.ydb_session_pool.retry_operation_sync,
            callee = execute,
        )

    @staticmethod
    def _to_model(row: dict[str, Any]) -> ChatState:
        return ChatState(
            chat_id = row[Column.CHAT_ID],
            phase = ChatPhase(row[Column.PHASE]),
            version = row[Column.VERSION],
            phase_version = row[Column.PHASE_VERSION],
            pending_message_ids = tuple(json.loads(row[Column.PENDING_MESSAGE_IDS])),
            updated_at = datetime.fromtimestamp(
                row[Column.UPDATED_AT] / 1_000_000,
                tz = timezone.utc,
            ),
        )
