from aiogram_i18n import I18nContext, I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore
from dishka import Provider, Scope, provide

DEFAULT_LOCALE = "ru"


class StandaloneI18nProvider(Provider):
    """
    I18nContext вне апдейта aiogram (webhook, шаги очереди, cron).
    Локаль по умолчанию, core загружается один раз на контейнер.
    """

    @provide(scope = Scope.APP)
    async def get_i18n_middleware(self) -> I18nMiddleware:
        i18n_middleware = I18nMiddleware(
            core = FluentRuntimeCore(
                path = "bot/resource/locales/{locale}",
                default_locale = DEFAULT_LOCALE,
            ),
            default_locale = DEFAULT_LOCALE,
        )
        await i18n_middleware.core.startup()
        return i18n_middleware

    @provide(scope = Scope.REQUEST)
    def get_i18n_context(
        self,
        i18n_middleware: I18nMiddleware,
    ) -> I18nContext:
        return i18n_middleware.new_context(
            locale = DEFAULT_LOCALE,
            data = {},
        )
