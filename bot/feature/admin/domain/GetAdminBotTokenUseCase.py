from bot.core.domain.const.env_const import TELEGRAM_BOT_TOKEN_ADMIN, \
    DEBUG_MODE_TOKEN, TELEGRAM_BOT_TOKEN_ADMIN_RELEASE


class GetAdminBotTokenUseCase:

    @staticmethod
    def invoke() -> str:
        return TELEGRAM_BOT_TOKEN_ADMIN \
            if DEBUG_MODE_TOKEN else TELEGRAM_BOT_TOKEN_ADMIN_RELEASE
