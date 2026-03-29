from bot.feature.business.data.repository.BotRepositoryImpl import BotRepositoryImpl
from bot.feature.business.domain.model.UserMessageInfoForAiModel import \
    UserMessageInfoForAiModel
from bot.feature.business.domain.scenario.GenerateAiReponseScenario import \
    GenerateAiResponseScenario
from bot.feature.business.domain.usecase.GetInactiveChatListUseCase import \
    GetInactiveChatListUseCase


class ReminderService:

    def __init__(
        self,
        generate_ai_response_scenario: GenerateAiResponseScenario,
        get_inactive_chat_list_use_case: GetInactiveChatListUseCase,
        bot_repository: BotRepositoryImpl,
    ):
        self.generate_ai_response_scenario = generate_ai_response_scenario
        self.get_inactive_chat_list_use_case = get_inactive_chat_list_use_case
        self.bot_repository = bot_repository

    async def invoke(self):
        inactive_chat_list = await self.get_inactive_chat_list_use_case.invoke()

        for chat in inactive_chat_list:
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

            bot_repository
