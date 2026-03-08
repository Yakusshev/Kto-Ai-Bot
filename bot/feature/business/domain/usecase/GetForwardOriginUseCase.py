import logging

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
        user_info: UserMessageInfoForAiModel,
        origin: ForwardOriginState | None,
    ) -> str:

        logging.info(f"owner_info = {owner_info}")
        logging.info(f"user_info = {user_info}")
        logging.info(f"origin = {origin}")

        if isinstance(origin, ForwardOriginUserModel):

            if owner_info.id == origin.id:
                return self.strings.forwarded_user_owner(
                    user_full_name = user_info.full_name,
                )
            elif user_info.chat_id == origin.id:
                #TODO не работает
                return self.strings.forwarded_user_self(
                    user_full_name = user_info.full_name,
                )
            else:
                return self.strings.forwarded_user(
                    user_full_name = user_info.full_name,
                    origin_full_name = origin.full_name,
                    origin_username = origin.username,
                )
        elif isinstance(origin, ForwardOriginHiddenUserModel):
            return self.strings.forwarded_hidden_user(
                user_full_name = user_info.full_name,
            )
        elif isinstance(origin, ForwardOriginChatModel):
            return self.strings.forwarded_chat(
                user_full_name = user_info.full_name,
            )

        elif isinstance(origin, ForwardOriginChannelModel):
            return self.strings.forwarded_channel(
                user_full_name = user_info.full_name,
                channel_username = origin.full_name,
                channel_title = origin.title,
            )
        return ""
