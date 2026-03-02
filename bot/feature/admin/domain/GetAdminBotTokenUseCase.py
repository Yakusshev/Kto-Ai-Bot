from bot.core.domain.const.env_const import TELEGRAM_BOT_TOKEN_ADMIN


class GetAdminBotTokenUseCase:

    @staticmethod
    def invoke() -> str:
        return TELEGRAM_BOT_TOKEN_ADMIN
