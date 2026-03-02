from bot.core.entry.BotManager import BotManager
from bot.feature.business.domain.get_bot_token import get_user_bot_token

user_bot_manager = BotManager(token = get_user_bot_token(), name = "User Bot")