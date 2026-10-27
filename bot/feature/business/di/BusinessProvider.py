from dishka import Provider, Scope, alias, provide, provide_all

from bot.feature.business.data.datasource.ChatStateRemoteDataSource import \
    ChatStateRemoteDataSource
from bot.feature.business.data.datasource.LocalDataSource import LocalDataSource
from bot.feature.business.data.datasource.TelegramRemoteDataSource import \
    TelegramRemoteDataSource
from bot.feature.business.data.datasource.UserRemoteDataSource import \
    UserRemoteDataSource
from bot.feature.business.data.repository.BotRepositoryImpl import BotRepositoryImpl
from bot.feature.business.data.repository.ChatHistoryRepositoryImpl import \
    ChatHistoryRepositoryImpl
from bot.feature.business.data.repository.ChatStateRepositoryImpl import \
    ChatStateRepositoryImpl
from bot.feature.business.data.repository.UserRepositoryImpl import \
    UserRepositoryImpl
from bot.feature.business.di.llm_module import get_llm_repository
from bot.feature.business.domain.repository.AiRepository import AiRepository
from bot.feature.business.domain.repository.BotRepository import BotRepository
from bot.feature.business.domain.repository.ChatStateRepository import \
    ChatStateRepository
from bot.feature.business.domain.scenario.GenerateAiReponseScenario import \
    GenerateAiResponseScenario
from bot.feature.business.domain.usecase.ApplyChatEventUseCase import \
    ApplyChatEventUseCase
from bot.feature.business.domain.usecase.DecideChatTransitionUseCase import \
    DecideChatTransitionUseCase
from bot.feature.business.domain.usecase.GetChatStrListUseCase import \
    GetChatInfoTupleUseCase
from bot.feature.business.domain.usecase.GetForwardOriginTextForAiUseCase import \
    GetForwardOriginTextForAiUseCase
from bot.feature.business.domain.usecase.GetInactiveChatListUseCase import \
    GetInactiveChatListUseCase
from bot.feature.business.domain.usecase.GetSystemInstructionUseCase import \
    GetSystemInstructionUseCase
from bot.feature.business.domain.usecase.GetUserListUseCase import GetUserListUseCase
from bot.feature.business.domain.usecase.HandleAiResponseUseCase import \
    HandleAiResponseUseCase
from bot.feature.business.domain.usecase.IsChatStepActualUseCase import \
    IsChatStepActualUseCase
from bot.feature.business.domain.usecase.SaveMessageUseCase import SaveMessageUseCase
from bot.feature.business.domain.usecase.SendAiRequestUseCase import \
    SendAiRequestUseCase
from bot.feature.business.domain.usecase.TypingLoopUseCase import TypingLoopUseCase
from bot.feature.business.domain.usecase.UpdateUserTableFromChatHistoryUseCase import \
    UpdateUserTableFromChatHistoryUseCase
from bot.feature.business.entrypoint.service.ChatService import ChatService
from bot.feature.business.entrypoint.service.ReminderService import ReminderService


class BusinessProvider(Provider):
    """
    Зависимости фичи business.
    APP: репозитории и источники данных (без состояния апдейта).
    REQUEST: use case и сервисы, которым нужны Strings.
    YDB driver / session pool берутся из CoreProvider.
    """

    # Data-слой: один экземпляр на приложение
    data_layer = provide_all(
        TelegramRemoteDataSource,
        UserRemoteDataSource,
        ChatHistoryRepositoryImpl,
        UserRepositoryImpl,
        BotRepositoryImpl,
        ChatStateRemoteDataSource,
        scope = Scope.APP,
    )

    # Состояние диалога в YDB (порт из domain -> реализация из data)
    chat_state_repository = provide(
        ChatStateRepositoryImpl,
        provides = ChatStateRepository,
        scope = Scope.APP,
    )

    # Действия бота в Telegram (порт из domain -> реализация из data)
    bot_repository = alias(source = BotRepositoryImpl, provides = BotRepository)

    @provide(scope = Scope.APP)
    def get_local_data_source(self) -> LocalDataSource:
        # Синглтон на уровне класса: все экземпляры делят одного владельца
        return LocalDataSource()

    @provide(scope = Scope.APP)
    def get_ai_repository(self) -> AiRepository:
        return get_llm_repository()

    # Domain и сервисы: зависят от Strings, поэтому REQUEST
    domain_layer = provide_all(
        HandleAiResponseUseCase,
        GetForwardOriginTextForAiUseCase,
        GetSystemInstructionUseCase,
        SendAiRequestUseCase,
        GenerateAiResponseScenario,
        SaveMessageUseCase,
        GetChatInfoTupleUseCase,
        GetInactiveChatListUseCase,
        GetUserListUseCase,
        UpdateUserTableFromChatHistoryUseCase,
        TypingLoopUseCase,
        DecideChatTransitionUseCase,
        ApplyChatEventUseCase,
        IsChatStepActualUseCase,
        ChatService,
        ReminderService,
        scope = Scope.REQUEST,
    )
