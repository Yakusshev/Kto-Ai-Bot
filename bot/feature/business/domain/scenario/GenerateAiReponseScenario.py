from typing import List

from bot.feature.business.domain.model.SaveMessageModel import OwnerModel
from bot.feature.business.domain.model.UserMessageInfoForAiModel import \
    UserMessageInfoForAiModel
from bot.feature.business.domain.usecase.GetSystemInstructionUseCase import \
    GetSystemInstructionUseCase
from bot.feature.business.domain.usecase.HandleAiResponseUseCase import \
    HandleAiResponseUseCase
from bot.feature.business.domain.usecase.SendAiRequestUseCase import \
    SendAiRequestUseCase


class GenerateAiResponseScenario:

    def __init__(
        self,
        send_ai_request_use_case: SendAiRequestUseCase,
        handle_ai_response_use_case: HandleAiResponseUseCase,
        get_system_instruction_use_case: GetSystemInstructionUseCase,
    ):
        self.send_ai_request_use_case = send_ai_request_use_case
        self.handle_ai_response_use_case = handle_ai_response_use_case
        self.get_system_instruction_use_case = get_system_instruction_use_case

    async def invoke(
        self,
        user_for_ai_model: UserMessageInfoForAiModel,
        owner_model: OwnerModel,
    ) -> List[str]:
        response = await self.send_ai_request_use_case.invoke(
            user_for_ai_model = user_for_ai_model,
            system_prompt = self.get_system_instruction_use_case.invoke(
                info = user_for_ai_model,
            ),
            owner_model = owner_model,
        )

        message_list = await self.handle_ai_response_use_case.invoke(response)

        return message_list
