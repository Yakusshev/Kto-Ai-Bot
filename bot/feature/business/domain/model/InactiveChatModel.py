from dataclasses import dataclass

from bot.feature.business.domain.model.ChatInfoModel import ChatInfoModel
from bot.feature.business.domain.model.UserModel import UserModel


@dataclass(frozen = True)
class InactiveChatModel:
    user_model: UserModel
    chat_info_model: ChatInfoModel