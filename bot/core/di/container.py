from dishka import AsyncContainer, Provider, make_async_container

from bot.core.di.CoreProvider import CoreProvider
from bot.feature.admin.di.AdminProvider import AdminProvider
from bot.feature.business.di.BusinessProvider import BusinessProvider
from bot.feature.business.di.ChatStepProvider import ChatStepProvider


def create_container(
    *context_providers: Provider,
) -> AsyncContainer:
    """
    Единственное место сборки DI. Контекстные провайдеры задаёт точка входа:
    для aiogram - AiogramProvider и AiogramI18nProvider, вне апдейта - StandaloneI18nProvider.
    """
    return make_async_container(
        CoreProvider(),
        BusinessProvider(),
        ChatStepProvider(),
        AdminProvider(),
        *context_providers,
    )
