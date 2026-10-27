"""
Сквозные тесты шагов ответа на реальном ChatStateRepositoryImpl и локальной YDB
(гонки экземпляров контейнера). Запуск YDB и переменные - как в ChatStateRepositoryImplTest;
без доступной YDB тесты пропускаются.
"""
import asyncio
import os
import uuid
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
from bot.feature.business.domain.model.ChatState import ChatPhase  # noqa: E402
from bot.feature.business.domain.model.ChatStep import ChatStepKind  # noqa: E402
from ..domain.fake.ChatStepHarness import CHAT_ID, ChatStepHarness  # noqa: E402

ENDPOINT = os.environ.get("YDB_TEST_ENDPOINT", "grpc://localhost:2136")
DATABASE = os.environ.get("YDB_TEST_DATABASE", "/local")


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
async def repository(session_pool: ydb.SessionPool) -> ChatStateRepositoryImpl:
    source = ChatStateRemoteDataSource(ydb_session_pool = session_pool)
    # Своя таблица на каждый тест: тесты не мешают друг другу
    source.table_name = f"chat_state_test_{uuid.uuid4().hex[:8]}"
    return ChatStateRepositoryImpl(chat_state_remote_data_source = source)


class TestChatStepsOnYdb:

    @pytest.mark.asyncio
    async def test_when_message_expect_full_chain_and_idle_in_ydb(
        self,
        repository: ChatStateRepositoryImpl,
    ):
        instance = ChatStepHarness(state_repository = repository)

        await instance.user_message(message_id = 1)
        await instance.run_all()

        assert instance.bot.sent_text_list == ["ответ"]
        assert (await repository.get(chat_id = CHAT_ID)).phase == ChatPhase.IDLE

    @pytest.mark.asyncio
    async def test_when_two_instances_get_messages_at_once_expect_one_timer_and_one_answer(
        self,
        repository: ChatStateRepositoryImpl,
    ):
        first = ChatStepHarness(state_repository = repository)
        second = ChatStepHarness(state_repository = repository)

        await asyncio.gather(
            first.user_message(message_id = 1),
            second.user_message(message_id = 2),
        )
        timer_list = first.queue.payload_list + second.queue.payload_list
        assert [p.kind for p in timer_list] == [ChatStepKind.READ_MESSAGE]

        owner = first if first.queue.payload_list else second
        await owner.run_all()

        assert owner.bot.sent_text_list == ["ответ"]
        assert owner.bot.action_list[0] in (('read', 1), ('read', 2))
        state = await repository.get(chat_id = CHAT_ID)
        assert state.phase == ChatPhase.IDLE

    @pytest.mark.asyncio
    async def test_when_owner_replies_while_read_step_runs_expect_no_answer(
        self,
        repository: ChatStateRepositoryImpl,
    ):
        instance = ChatStepHarness(state_repository = repository)
        other_instance = ChatStepHarness(state_repository = repository)
        await instance.user_message(message_id = 1)

        await asyncio.gather(
            instance.run_next(),
            other_instance.owner_message(),
        )
        await instance.run_all()

        assert instance.bot.sent_text_list == []
        assert (await repository.get(chat_id = CHAT_ID)).phase == ChatPhase.IDLE

    @pytest.mark.asyncio
    async def test_when_message_arrives_on_other_instance_during_answering_expect_old_answer_dropped(
        self,
        repository: ChatStateRepositoryImpl,
    ):
        instance = ChatStepHarness(state_repository = repository)
        other_instance = ChatStepHarness(state_repository = repository)
        await instance.user_message(message_id = 1)
        await instance.run_next()
        await instance.run_next()

        await other_instance.user_message(message_id = 2)
        await instance.run_all()
        await other_instance.run_all()

        assert instance.bot.sent_text_list == []
        assert other_instance.bot.sent_text_list == ["ответ"]
        assert (await repository.get(chat_id = CHAT_ID)).phase == ChatPhase.IDLE
