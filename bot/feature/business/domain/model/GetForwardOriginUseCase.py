from bot.feature.business.domain.model.ForwardOriginState import ForwardOriginState, \
    ForwardOriginUserModel, ForwardOriginHiddenUserModel, ForwardOriginChatModel, \
    ForwardOriginChannelModel
from bot.feature.business.domain.model.UserMessageInfoForAiModel import \
    UserMessageInfoForAiModel
from bot.resource.Strings import Strings


class GetForwardOriginUseCase:

    def __init__(
        self,
        strings: Strings,
    ):
        self.strings = strings


    def invoke(
        self,
        owner_info: UserMessageInfoForAiModel,
        origin: ForwardOriginState | None,
    ) -> str:

        if origin is None:
            return ""

        if origin is ForwardOriginUserModel:
            return self.strings.forwarded_user(
                owner_full_name = owner_info.full_name,
                origin_full_name = origin.full_name,
                origin_username = origin.username,
            )
        elif origin is ForwardOriginHiddenUserModel:
            return self.strings.forwarded_user(
                owner_full_name = owner_info.full_name,
                origin_full_name = origin.full_name,
                origin_username = origin.username,
            )
        elif origin is ForwardOriginChatModel:
            return self.strings.forwarded_chat(
                owner_full_name = owner_info.full_name,
            )
        elif origin is ForwardOriginChannelModel:
            return self.strings.forwarded_channel(
                owner_full_name = owner_info.full_name,
                channel_username = origin.username,
            )
        return ""
