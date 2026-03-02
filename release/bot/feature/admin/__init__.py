from bot.core.entry.BotManager import BotManager
from bot.feature.admin.domain.GetAdminBotTokenUseCase import GetAdminBotTokenUseCase
from bot.feature.business.domain.get_bot_token import get_user_bot_token


admin_bot_manager = BotManager(
    token = GetAdminBotTokenUseCase.invoke(),
    name = "Admin Bot",
)