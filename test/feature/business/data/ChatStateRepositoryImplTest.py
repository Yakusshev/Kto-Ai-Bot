"""
Интеграционные тесты ChatStateRepositoryImpl на локальной YDB.

Запуск локальной YDB:
    docker run -d --name ydb-local -p 2136:2136 -h localhost -e GRPC_PORT=2136 \
        -e YDB_USE_IN_MEMORY_PDISKS=true ydbplatform/local-ydb:latest
Адрес меняется переменными YDB_TEST_ENDPOINT (по умолчанию grpc://localhost:2136)
и YDB_TEST_DATABASE (по умолчанию /local). Если YDB недоступна - тесты пропускаются.
"""
import asyncio
import os
import uuid
from datetime import datetime, timezone
from typing import Iterator

import pytest
import pytest_asyncio

# env_const валидирует окружение при импорте (как в CI)
for _key, _value in {
    "DEBUG_MODE_TOKEN": "True",
    "BOT_TOKEN": "0:test",
    "BOT_TOKEN_ADMIN": "0:test",
    "YDB_ENDPOINT": "grpc://localhost:2136",
    "YDB_PATH": "/local",
    "NEXT_MESSAGE_SEPARATOR": "|||",
    "ADMIN_ID_LIST": "1",
    "OWN_CHANNEL_ID": "1",
    "OWN_CHAT_ID": "1",
}.items():
    os.environ.setdefault(_key, _value)

import ydb  # noqa: E402

from bot.feature.business.data.datasource.ChatStateRemoteDataSource import \
    ChatStateRemoteDataSource  # noqa: E402
from bot.feature.business.data.repository.ChatStateRepositoryImpl import \
    ChatStateRepositoryImpl  # noqa: E402
from bot.feature.business.domain.model.ChatDecision import ChatAction  # noqa: E402
from bot.feature.business.domain.model.ChatEvent import (  # noqa: E402
    ChatEvent,
    ChatEventKind,
)
from bot.feature.business.domain.model.ChatState import (  # noqa: E402
    ChatPhase,
    ChatState,
)
from bot.feature.business.domain.usecase.ApplyChatEventUseCase import \
    ApplyChatEventUseCase  # noqa: E402
from bot.feature.business.domain.usecase.DecideChatTransitionUseCase import \
    DecideChatTransitionUseCase  # noqa: E402

ENDPOINT = os.environ.get("YDB_TEST_ENDPOINT", "grpc://localhost:2136")
DATABASE = os.environ.get("YDB_TEST_DATABASE", "/local")
CHAT_ID = 42


def _state(
    version: int,
    phase: ChatPhase = ChatPhase.PREPARING,
) -> ChatState:
    return ChatState(
        chat_id = CHAT_ID,
        phase = phase,
        version = version,
        phase_version = version,
        pending_message_ids = (1, 2),
        updated_at = datetime(2026, 1, 1, 12, 0, 0, 123456, tzinfo = timezone.utc),
    )


@pytest.fixture(scope = "module")
def session_pool() -> Iterator[ydb.SessionPool]:
    driver = ydb.Driver(endpoint = ENDPOINT, database = DATABASE)
    try:
        driver.wait(timeout = 5, fail_fast = True)
    except Exception:
        driver.stop()
        pytest.skip(f"Локальная YDB недоступна ({ENDPOINT}{DATABASE})")

    pool = ydb.SessionPool(driver)
    yield pool
    pool.stop()
    driver.stop()


@pytest_asyncio.fixture
async def data_source(session_pool: ydb.SessionPool) -> ChatStateRemoteDataSource:
    source = ChatStateRemoteDataSource(ydb_session_pool = session_pool)
    # Своя таблица на каждый тест: тесты не мешают друг другу
    source.table_name = f"chat_state_test_{uuid.uuid4().hex[:8]}"
    return source


@pytest.fixture
def repository(data_source: ChatStateRemoteDataSource) -> ChatStateRepositoryImpl:
    return ChatStateRepositoryImpl(chat_state_remote_data_source = data_source)


class TestChatStateRepositoryImpl:

    @pytest.mark.asyncio
    async def test_when_no_row_expect_initial_idle_state(
        self,
        repository: ChatStateRepositoryImpl,
    ):
        state = await repository.get(chat_id = CHAT_ID)

        assert state.phase == ChatPhase.IDLE
        assert state.version == 0

    @pytest.mark.asyncio
    async def test_when_saved_expect_state_read_back_equal(
        self,
        repository: ChatStateRepositoryImpl,
    ):
        expected = _state(version = 1)

        assert await repository.compare_and_set(expected_version = 0, new_state = expected)

        assert await repository.get(chat_id = CHAT_ID) == expected

    @pytest.mark.asyncio
    async def test_when_version_is_outdated_expect_write_rejected(
        self,
        repository: ChatStateRepositoryImpl,
    ):
        await repository.compare_and_set(expected_version = 0, new_state = _state(1))
        await repository.compare_and_set(expected_version = 1, new_state = _state(2))

        is_written = await repository.compare_and_set(
            expected_version = 1,
            new_state = _state(2, ChatPhase.ANSWERING),
        )

        assert not is_written
        assert (await repository.get(chat_id = CHAT_ID)).phase == ChatPhase.PREPARING

    @pytest.mark.asyncio
    async def test_when_parallel_writes_same_version_expect_exactly_one_wins(
        self,
        repository: ChatStateRepositoryImpl,
    ):
        results = await asyncio.gather(
            *[
                repository.compare_and_set(expected_version = 0, new_state = _state(1))
                for _ in range(5)
            ],
        )

        assert results.count(True) == 1
        assert (await repository.get(chat_id = CHAT_ID)).version == 1

    @pytest.mark.asyncio
    async def test_when_two_messages_race_expect_version_2_and_single_timer(
        self,
        repository: ChatStateRepositoryImpl,
    ):
        use_case = ApplyChatEventUseCase(
            chat_state_repository = repository,
            decide_chat_transition_use_case = DecideChatTransitionUseCase(),
        )

        first, second = await asyncio.gather(
            use_case.invoke(
                CHAT_ID,
                ChatEvent(kind = ChatEventKind.USER_MESSAGE, message_id = 1),
            ),
            use_case.invoke(
                CHAT_ID,
                ChatEvent(kind = ChatEventKind.USER_MESSAGE, message_id = 2),
            ),
        )

        # Оба сообщения учтены (version 0 -> 2), таймер запущен ровно один раз
        state = await repository.get(chat_id = CHAT_ID)
        assert state.version == 2
        assert state.phase == ChatPhase.PREPARING
        assert sorted(state.pending_message_ids) == [1, 2]
        actions = sorted([first.action, second.action])
        assert actions == sorted([ChatAction.START_PREPARING, ChatAction.NONE])
