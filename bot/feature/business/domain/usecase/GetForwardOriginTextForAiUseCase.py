import logging

from bot.core.domain.const.env_const import OWN_CHAT_ID, OWN_CHANNEL_ID
from bot.feature.business.domain.model.ForwardOriginState import ForwardOriginState, \
    ForwardOriginUserModel, ForwardOriginHiddenUserModel, ForwardOriginChatModel, \
    ForwardOriginChannelModel
from bot.feature.business.domain.model.SaveMessageModel import OwnerModel, \
    MessageRole
from bot.feature.business.domain.model.UserMessageInfoForAiModel import \
    UserMessageInfoForAiModel
from bot.resource.Strings import Strings


class GetForwardOriginTextForAiUseCase:

    def __init__(
        self,
        strings: Strings,
    ):
        self.strings = strings

    def invoke(
        self,
        role: MessageRole,
        owner_info: OwnerModel,
        user_info: UserMessageInfoForAiModel,
        origin: ForwardOriginState | None,
    ) -> str:

        logging.info(f"owner_info = {owner_info}")
        logging.info(f"user_info = {user_info}")
        logging.info(f"origin = {origin}")

        author = user_info.full_name \
            if role == MessageRole.USER \
            else self.strings.you()

        if isinstance(origin, ForwardOriginUserModel):
            return self.handle_user(
                author = author,
                owner_info = owner_info,
                user_info = user_info,
                origin = origin,
            )
        elif isinstance(origin, ForwardOriginHiddenUserModel):
            return self.strings.forwarded_hidden_user(
                author_name = author,
                origin_full_name = origin.full_name,
            )
        elif isinstance(origin, ForwardOriginChatModel):
            return self.handle_chat(
                author = author,
                origin = origin,
            )
        elif isinstance(origin, ForwardOriginChannelModel):
            return self.handle_channel(
                author = author,
                origin = origin,
            )
        else:
            return ""

    def handle_user(
        self,
        owner_info: OwnerModel,
        author: str,
        user_info: UserMessageInfoForAiModel,
        origin: ForwardOriginUserModel,
    ) -> str:
        if owner_info.id == origin.id:
            return self.strings \
                .forwarded_user_owner(author_name = author)
        elif user_info.chat_id == origin.id:
            return self.strings \
                .forwarded_user_self(author_name = author)
        elif origin.bot:
            return self.strings.forwarded_bot(
                author_name = author,
                origin_full_name = origin.full_name,
                origin_username = origin.username,
            )
        else:
            return self.strings.forwarded_user(
                author_name = author,
                origin_full_name = origin.full_name,
                origin_username = origin.username,
            )

    def handle_chat(
        self,
        author: str,
        origin: ForwardOriginChatModel,
    ):
        if origin.id == OWN_CHAT_ID:
            return self.strings \
                .forwarded_own_chat(author_name = author)
        else:
            return self.strings.forwarded_chat(
                author_name = author,
                title = origin.title,
                username = origin.username,
            )

    def handle_channel(
        self,
        author: str,
        origin: ForwardOriginChannelModel,
    ):
        if origin.id == OWN_CHANNEL_ID:
            return self.strings \
                .forwarded_own_channel(author_name = author)
        else:
            return self.strings.forwarded_channel(
                author_name = author,
                channel_username = origin.username,
                channel_title = origin.title,
            )
