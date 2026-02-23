from bot.domain.const.env_const import DEBUG_MODE, TELEGRAM_BOT_TOKEN_DEBUG, TELEGRAM_BOT_TOKEN_RELEASE


def get_bot_token() -> str:
    if DEBUG_MODE:
        return TELEGRAM_BOT_TOKEN_DEBUG
    else:
        return TELEGRAM_BOT_TOKEN_RELEASE