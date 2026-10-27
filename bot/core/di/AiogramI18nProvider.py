from aiogram_i18n import I18nContext
from dishka import Provider, Scope, provide
from dishka.integrations.aiogram import AiogramMiddlewareData


class AiogramI18nProvider(Provider):
    """I18nContext из апдейта aiogram: его кладёт в data стандартный I18nMiddleware."""

    @provide(scope = Scope.REQUEST)
    def get_i18n_context(
        self,
        data: AiogramMiddlewareData,
    ) -> I18nContext:
        i18n = data.get("i18n")
        if i18n is None:
            raise RuntimeError(
                "I18nContext не найден в data. "
                "Убедитесь, что I18nMiddleware подключён до setup_dishka.",
            )
        return i18n  # type: ignore[no-any-return]
