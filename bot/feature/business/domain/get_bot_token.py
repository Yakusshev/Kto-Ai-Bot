from bot.core.domain.const.env_const import TELEGRAM_BOT_TOKEN_DEBUG, \
    DEBUG_MODE_TOKEN, TELEGRAM_BOT_TOKEN_RELEASE


def get_user_bot_token() -> str:
    if DEBUG_MODE_TOKEN:
        return TELEGRAM_BOT_TOKEN_DEBUG
    else:
        return TELEGRAM_BOT_TOKEN_RELEASE