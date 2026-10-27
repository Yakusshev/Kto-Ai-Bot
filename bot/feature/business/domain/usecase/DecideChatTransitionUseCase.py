from dataclasses import replace
from datetime import datetime

from bot.feature.business.domain.model.ChatDecision import ChatAction, ChatDecision
from bot.feature.business.domain.model.ChatEvent import ChatEvent, ChatEventKind
from bot.feature.business.domain.model.ChatState import ChatPhase, ChatState


class DecideChatTransitionUseCase:
    """
    Чистая функция переходов диалога: (состояние, событие) -> (новое состояние, действие).

    Любой переход с записью повышает version (оптимистичная блокировка), а phase_version
    меняется только при старте новой фазы по сообщению.

    Переходы:
        idle      + сообщение -> preparing (version+1, запустить таймер)
        preparing + сообщение -> preparing (version+1, сообщение копится, таймер не сбрасывается)
        answering + сообщение -> answering (version+1, отмена и ответ сразу на всё)
        любая фаза + ответ владельца -> idle (version+1, отмена)
        idle + напоминание -> answering; в других фазах напоминание игнорируется
        preparing -> answering и answering -> idle - по событиям отложенных шагов,
        если талон шага не устарел (иначе STALE и состояние не меняется)
    """

    def invoke(
        self,
        state: ChatState,
        event: ChatEvent,
        now: datetime,
    ) -> ChatDecision:
        match event.kind:
            case ChatEventKind.USER_MESSAGE:
                return self._on_user_message(state, event, now)
            case ChatEventKind.OWNER_MESSAGE:
                return self._on_owner_message(state, now)
            case ChatEventKind.REMIND:
                return self._on_remind(state, now)
            case ChatEventKind.PREPARING_FINISHED:
                return self._on_preparing_finished(state, event, now)
            case ChatEventKind.ANSWER_FINISHED:
                return self._on_answer_finished(state, event, now)

    @staticmethod
    def _on_user_message(
        state: ChatState,
        event: ChatEvent,
        now: datetime,
    ) -> ChatDecision:
        version = state.version + 1
        pending = (event.message_id,) if event.message_id is not None else ()

        if state.phase == ChatPhase.PREPARING:
            # Таймер не сбрасывается: phase_version прежний
            return ChatDecision(
                state = replace(
                    state,
                    version = version,
                    pending_message_ids = state.pending_message_ids + pending,
                    updated_at = now,
                ),
                action = ChatAction.NONE,
            )

        # idle: начинаем подготовку; answering: отменяем текущий ответ и отвечаем сразу.
        # В обоих случаях начинается новая фаза, старые талоны устаревают.
        is_answering = state.phase == ChatPhase.ANSWERING
        return ChatDecision(
            state = replace(
                state,
                phase = ChatPhase.ANSWERING if is_answering else ChatPhase.PREPARING,
                version = version,
                phase_version = version,
                pending_message_ids = pending,
                updated_at = now,
            ),
            action = ChatAction.CANCEL_AND_ANSWER_NOW
            if is_answering else ChatAction.START_PREPARING,
        )

    @staticmethod
    def _on_owner_message(
        state: ChatState,
        now: datetime,
    ) -> ChatDecision:
        version = state.version + 1
        return ChatDecision(
            state = replace(
                state,
                phase = ChatPhase.IDLE,
                version = version,
                phase_version = version,
                pending_message_ids = (),
                updated_at = now,
            ),
            action = ChatAction.NONE
            if state.phase == ChatPhase.IDLE else ChatAction.CANCEL,
        )

    @staticmethod
    def _on_remind(
        state: ChatState,
        now: datetime,
    ) -> ChatDecision:
        if state.phase != ChatPhase.IDLE:
            return ChatDecision(state = state, action = ChatAction.STALE)

        version = state.version + 1
        return ChatDecision(
            state = replace(
                state,
                phase = ChatPhase.ANSWERING,
                version = version,
                phase_version = version,
                pending_message_ids = (),
                updated_at = now,
            ),
            action = ChatAction.START_ANSWER,
        )

    @staticmethod
    def _on_preparing_finished(
        state: ChatState,
        event: ChatEvent,
        now: datetime,
    ) -> ChatDecision:
        if event.ticket is None or not state.is_actual(event.ticket) \
            or state.phase != ChatPhase.PREPARING:
            return ChatDecision(state = state, action = ChatAction.STALE)

        # version растёт при любой записи (на этом держится CAS: два экземпляра не могут
        # оба «завершить» один шаг). Талон preparing устаревает из-за смены фазы.
        return ChatDecision(
            state = replace(
                state,
                phase = ChatPhase.ANSWERING,
                version = state.version + 1,
                updated_at = now,
            ),
            action = ChatAction.START_ANSWER,
        )

    @staticmethod
    def _on_answer_finished(
        state: ChatState,
        event: ChatEvent,
        now: datetime,
    ) -> ChatDecision:
        if event.ticket is None or not state.is_actual(event.ticket) \
            or state.phase != ChatPhase.ANSWERING:
            return ChatDecision(state = state, action = ChatAction.STALE)

        return ChatDecision(
            state = replace(
                state,
                phase = ChatPhase.IDLE,
                version = state.version + 1,
                pending_message_ids = (),
                updated_at = now,
            ),
            action = ChatAction.NONE,
        )
