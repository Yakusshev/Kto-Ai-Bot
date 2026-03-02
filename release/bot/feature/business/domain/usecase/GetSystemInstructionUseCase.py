from bot.core.domain.const.env_const import NEXT_MESSAGE_SEPARATOR
from bot.feature.business.domain.model.UserMessageInfoForAiModel import UserMessageInfoForAiModel
from bot.resource.Strings import Strings
from datetime import datetime


class GetSystemInstructionUseCase:
    strings: Strings

    def __init__(
        self,
        strings: Strings,
    ):
        self.strings = strings

    def invoke(
        self,
        info: UserMessageInfoForAiModel,
    ) -> str:
        return self.strings.system_instruction(
            username = info.username,
            full_name = info.full_name,
            date_and_time = GetSystemInstructionUseCase \
                .format_time(message_datetime = info.datetime),
            message_separator = NEXT_MESSAGE_SEPARATOR,
        )

    @staticmethod
    def format_time(
        message_datetime: datetime,
    ):
        time_readable = message_datetime.strftime("%Y-%m-%d %A %H:%M")

        print("GetSystemInstructionUseCase.time_readable ", time_readable)

        return time_readable
