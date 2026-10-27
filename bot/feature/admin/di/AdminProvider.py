from dishka import Provider, Scope, provide_all

from bot.feature.admin.domain.FormatUserChatModelListUseCase import \
    FormatUserChatModelListUseCase
from bot.feature.admin.domain.scenario.GetRemindInfoTextScenario import \
    GetRemindInfoTextScenario


class AdminProvider(Provider):
    """
    Зависимости фичи admin. GetInactiveChatListUseCase приходит
    из BusinessProvider через общий контейнер, провайдеры фич друг друга не импортируют.
    """

    scenario_layer = provide_all(
        FormatUserChatModelListUseCase,
        GetRemindInfoTextScenario,
        scope = Scope.REQUEST,
    )
