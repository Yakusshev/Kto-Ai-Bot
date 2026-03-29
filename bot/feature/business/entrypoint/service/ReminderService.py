import asyncio
from asyncio import Event, Task

from aiogram.types import Message

from bot.feature.business.data.repository.BotRepositoryImpl import BotRepositoryImpl
from bot.feature.business.data.repository.TaskSchedulerRepositoryImpl import \
    TaskSchedulerRepositoryImpl
from bot.feature.business.domain.model.InactiveChatModel import InactiveChatModel
from bot.feature.business.domain.model.SaveMessageModel import SaveMessageModel, \
    MessageRole
from bot.feature.business.domain.model.UserMessageInfoForAiModel import \
    UserMessageInfoForAiModel
from bot.feature.business.domain.scenario.GenerateAiReponseScenario import \
    GenerateAiResponseScenario
from bot.feature.business.domain.usecase.GetInactiveChatListUseCase import \
    GetInactiveChatListUseCase
from bot.feature.business.domain.usecase.SaveMessageUseCase import SaveMessageUseCase
from bot.feature.business.domain.usecase.TypingLoopUseCase import TypingLoopUseCase
from bot.feature.business.entrypoint.HumanWaitingBehavior import \
    wait_to_write_message
from bot.feature.business.entrypoint.SaveMessageModelMapper import \
    to_save_message_model
from bot.util.log_util import get_logger


class ReminderService:

    def __init__(
        self,
        generate_ai_response_scenario: GenerateAiResponseScenario,
        get_inactive_chat_list_use_case: GetInactiveChatListUseCase,
        bot_repository: BotRepositoryImpl,
        task_scheduler: TaskSchedulerRepositoryImpl,
        typing_loop_use_case: TypingLoopUseCase,
        save_message_use_case: SaveMessageUseCase,
    ):
        self.generate_ai_response_scenario = generate_ai_response_scenario
        self.get_inactive_chat_list_use_case = get_inactive_chat_list_use_case
        self.bot_repository = bot_repository
        self.task_scheduler = task_scheduler
        self.typing_loop_use_case = typing_loop_use_case
        self.save_message_use_case = save_message_use_case

    async def invoke(self):

        inactive_chat_list = await self.get_inactive_chat_list_use_case.invoke()

        # for chat in inactive_chat_list:

        chat = inactive_chat_list[0]

        await self.__answer_message(chat = chat)

    async def __answer_message(
        self,
        chat: InactiveChatModel,
    ) -> None:
        task_key = str(chat.chat_info_model.id)

        if self.task_scheduler.is_task_exist(key = task_key):
            return

        stop_typing = asyncio.Event()
        typing_task = None

        message_chat_id = str()
        business_connection_id = chat.chat_info_model.business_connection_id
        answer_message_list: list[Message] = []

        try:
            stop_typing = asyncio.Event()
            typing_task = asyncio.create_task(
                self.typing_loop_use_case.invoke(
                    chat_id = chat.chat_info_model.id,
                    business_connection_id = business_connection_id,
                    stop_event = stop_typing,
                ),
            )

            response_list = await self.generate_ai_response_scenario.invoke(
                user_for_ai_model = UserMessageInfoForAiModel(
                    chat_id = chat.chat_info_model.id,
                    username = chat.user_model.username,
                    full_name = chat.user_model.full_name,
                    datetime = chat.chat_info_model.last_message_date,
                ),
                owner_model = await self.bot_repository.get_business_connection_owner(
                    id = chat.chat_info_model.business_connection_id,
                ),
            )

            for ai_answer in response_list:
                await wait_to_write_message(ai_answer)

                try:
                    if ai_answer:
                        sent = await self.bot_repository.send_message(
                            chat_id = chat.chat_info_model.id,
                            text = ai_answer,
                            business_connection_id = business_connection_id,
                        )
                        answer_message_list.append(sent)
                except Exception as e:
                    logger.error(
                        f"__answer_message EXCEPTION\n"
                        f"id = {chat.chat_info_model.id}\n"
                        f"chat = {chat}\n"
                        f"e = {e}",
                    )
                except asyncio.CancelledError as canceled_error:
                    raise canceled_error

        except asyncio.CancelledError:
            await self.complete_answer(
                answer_message_list = answer_message_list,
                stop_typing = stop_typing,
                typing_task = typing_task,
            )
            logger.info("__answer_message отменён: chat_id=%s", message_chat_id)
            raise

        finally:
            await self.complete_answer(
                answer_message_list = answer_message_list,
                stop_typing = stop_typing,
                typing_task = typing_task,
            )

    async def complete_answer(
        self,
        answer_message_list: list[Message],
        stop_typing: Event,
        typing_task: Task[None] | None,
    ):
        if stop_typing:
            stop_typing.set()
        if typing_task:
            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass
        # Сохраняем отправленные сообщения бота в БД (fire-and-forget)
        if answer_message_list:
            await self.save_assistant_text_message_list(
                message_list = answer_message_list,
            ),

    async def save_assistant_text_message_list(
        self,
        message_list: list[Message],
    ):
        save_message_model_list: list[SaveMessageModel] = []

        for message in message_list:
            save_message_model = to_save_message_model(
                message = message,
                content = message.text,
                role = MessageRole.ASSISTANT,
            )

            if save_message_model:
                save_message_model_list.append(save_message_model)
            else:
                logger.warning(
                    f"save_message: пустой text_content, message = {message}",
                )

        await self.save_message_use_case.invoke(
            save_message_model_list = save_message_model_list,
        ),

logger = get_logger(TypingLoopUseCase.__name__)