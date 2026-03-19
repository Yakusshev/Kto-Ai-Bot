import logging
import zoneinfo

from bot.core.domain.const.env_const import NEXT_MESSAGE_SEPARATOR
from bot.feature.business.domain.model.UserMessageInfoForAiModel import UserMessageInfoForAiModel
from bot.resource.Strings import Strings
from datetime import datetime

from bot.util.log_util import get_logger


class GetSystemInstructionUseCase():
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

        moscow_tz = zoneinfo.ZoneInfo("Europe/Moscow")
        moscow_now = datetime.now(moscow_tz)

        part1 = self.strings.system_instruction(
            username = info.username,
            full_name = info.full_name,
            date_and_time = GetSystemInstructionUseCase \
                .format_time(message_datetime = moscow_now),
        )

        part_ignore = self.strings.system_instruction_ignore()

        part2 = self.strings.system_instruction_part_2(
            message_separator = NEXT_MESSAGE_SEPARATOR,
        )

        part3 = self.strings.system_instruction_part_3(
            message_separator = NEXT_MESSAGE_SEPARATOR,
        )

        part_channel = self.strings.system_instruction_channel_lore()

        return f"{part1}\n{part_ignore}\n{part2}\n{part3}\n{part_channel}"

    @staticmethod
    def format_time(
        message_datetime: datetime,
    ):
        time_readable = message_datetime.strftime("%Y-%m-%d %A %H:%M")

        _logger.debug(f"format_time {time_readable}")

        return time_readable

_logger = get_logger(GetSystemInstructionUseCase.__name__)
