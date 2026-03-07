from bot.feature.business.domain.model.ForwardOriginState import ForwardOriginState, \
    ForwardOriginUserModel, ForwardOriginHiddenUserModel, ForwardOriginChatModel, \
    ForwardOriginChannelModel
from bot.feature.business.domain.model.SaveMessageModel import OwnerModel
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
        owner_info: OwnerModel,
        origin: ForwardOriginState | None,
    ) -> str:

        if origin is None:
            return ""
        elif isinstance(origin, ForwardOriginUserModel):
            return self.strings.forwarded_user(
                owner_full_name = owner_info.full_name,
                origin_full_name = origin.full_name,
                origin_username = origin.full_name,
            )
        elif isinstance(origin, ForwardOriginHiddenUserModel):
            return self.strings.forwarded_hidden_user(
                owner_full_name = owner_info.full_name,
                origin_full_name = origin.full_name,
            )
        elif isinstance(origin, ForwardOriginChatModel):
            return self.strings.forwarded_chat(
                owner_full_name = owner_info.full_name,
            )

        elif isinstance(origin, ForwardOriginChannelModel):
            return self.strings.forwarded_channel(
                owner_full_name = owner_info.full_name,
                channel_username = origin.full_name,
            )
        return ""
