from bot.feature.business.domain.usecase.FormatUserChatModelListUseCase import \
    FormatUserChatModelListUseCase
from bot.feature.business.domain.usecase.GetInactiveChatListUseCase import \
    GetInactiveChatListUseCase
from bot.util.log_util import get_logger


class GetRemindInfoTextScenario:

    def __init__(
        self,
        get_inactive_chat_list_use_case: GetInactiveChatListUseCase,
        format_user_chat_model_list_use_case: FormatUserChatModelListUseCase,
    ):
        self.get_inactive_chat_list_use_case = get_inactive_chat_list_use_case
        self.format_user_chat_model_list_use_case = format_user_chat_model_list_use_case

    async def invoke(self) -> list[str]:
        user_list = await self.get_inactive_chat_list_use_case.invoke()

        text_list = self.format_user_chat_model_list_use_case \
            .invoke(user_list = user_list)

        return text_list


_logger = get_logger(GetRemindInfoTextScenario.__name__)
