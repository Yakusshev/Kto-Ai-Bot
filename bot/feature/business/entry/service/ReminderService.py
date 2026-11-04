import asyncio

from bot.feature.admin.domain.CommandConst import CommandConst
from bot.feature.business.domain.model.ChatDecision import ChatAction
from bot.feature.business.domain.model.ChatEvent import ChatEvent, ChatEventKind
from bot.feature.business.domain.model.ChatStep import ChatStepContext
from bot.feature.business.domain.model.UserChatModel import UserChatModel
from bot.feature.business.domain.usecase.GetInactiveChatListUseCase import \
    GetInactiveChatListUseCase
from bot.feature.business.domain.usecase.ProcessChatEventUseCase import \
    ProcessChatEventUseCase
from bot.util.log_util import get_logger


class ReminderService:

    def __init__(
        self,
        get_inactive_chat_list_use_case: GetInactiveChatListUseCase,
        process_chat_event_use_case: ProcessChatEventUseCase,
    ):
        self.get_inactive_chat_list_use_case = get_inactive_chat_list_use_case
        self.process_chat_event_use_case = process_chat_event_use_case

    async def invoke(
        self,
        args: str,
    ) -> bool:

        if args == CommandConst.REMIND_ALL:
            await self.remind_all()
            return True
        else:
            return await self.remind(int(args))

    async def remind(
        self,
        id: int,
    ) -> bool:
        inactive_chat_list = await self.get_inactive_chat_list_use_case.invoke()

        user_chat = next(
            (user_chat
             for user_chat in inactive_chat_list
             if user_chat.chat_info_model.id == int(id)
             ),
            None,
        )

        if user_chat:
            await self.remind_task(chat = user_chat)
            return True
        else:
            return False

    async def remind_all(self):
        inactive_chat_list = await self.get_inactive_chat_list_use_case.invoke()

        task_list = [
            self.remind_task(chat = user_chat) for user_chat in inactive_chat_list
        ]

        for task in asyncio.as_completed(task_list):
            await task

    async def remind_task(self, chat: UserChatModel):
        """Запускает ответ по напоминанию: шаги ведёт очередь, как у входящего сообщения."""
        user = chat.user_model
        action = await self.process_chat_event_use_case.invoke(
            chat_id = chat.chat_info_model.id,
            event = ChatEvent(kind = ChatEventKind.REMIND),
            context = ChatStepContext(
                business_connection_id = chat.chat_info_model.business_connection_id,
                username = (user.username if user else None) or "",
                full_name = (user.full_name if user else None) or "",
                message_datetime = chat.chat_info_model.last_message_date,
                message_text = "",
                remind = True,
            ),
        )

        if action == ChatAction.STALE:
            _logger.warning(
                "remind: в чате chat_id=%s уже идёт диалог, напоминание пропущено",
                chat.chat_info_model.id,
            )


_logger = get_logger(ReminderService.__name__)
