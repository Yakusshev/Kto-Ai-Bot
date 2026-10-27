import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from beartype import beartype

from bot.feature.business.domain.model.ChatState import ChatPhase, StepTicket

# Версия формата сообщения очереди: при несовместимых изменениях поднимать
PAYLOAD_VERSION = 1


class ChatStepKind(StrEnum):
    """Шаги ответа бота; каждый выполняется отдельным сообщением очереди."""
    READ_MESSAGE = 'read_message'  # пометить сообщение прочитанным
    START_TYPING = 'start_typing'  # показать «печатает...» после паузы «на чтение»
    GENERATE_AND_SEND = 'generate_and_send'  # сгенерировать ответ и отправить


@beartype
@dataclass(frozen = True)
class ChatStepContext:
    """
    Всё, что нужно шагу, кроме талона: сообщение пользователя, на которое отвечаем.

    message_id - сообщение для отметки «прочитано» (None у напоминания).
    message_text - текст сообщения: от его длины зависит пауза «на чтение».
    remind - ответ по напоминанию, без входящего сообщения.
    """
    business_connection_id: str
    username: str
    full_name: str
    message_datetime: datetime
    message_text: str
    message_id: int | None = None
    remind: bool = False


@beartype
@dataclass(frozen = True)
class ChatStepPayload:
    """
    Сериализуемая задача отложенного шага (тело сообщения очереди).

    step_id - уникален для каждого запланированного шага и сохраняется при повторной
    доставке, поэтому по нему можно отличить дубль от нового шага.
    """
    step_id: str
    kind: ChatStepKind
    ticket: StepTicket
    context: ChatStepContext

    @property
    def chat_id(self) -> int:
        return self.ticket.chat_id

    def to_json(self) -> str:
        return json.dumps(
            {
                'v': PAYLOAD_VERSION,
                'step_id': self.step_id,
                'kind': self.kind.value,
                'chat_id': self.ticket.chat_id,
                'phase': self.ticket.phase.value,
                'phase_version': self.ticket.phase_version,
                'business_connection_id': self.context.business_connection_id,
                'message_id': self.context.message_id,
                'username': self.context.username,
                'full_name': self.context.full_name,
                'message_datetime': self.context.message_datetime.isoformat(),
                'message_text': self.context.message_text,
                'remind': self.context.remind,
            },
            ensure_ascii = False,
        )

    @staticmethod
    def from_json(body: str) -> 'ChatStepPayload':
        data = json.loads(body)
        if data.get('v') != PAYLOAD_VERSION:
            raise ValueError(f"Неизвестная версия задачи шага: {data.get('v')}")

        return ChatStepPayload(
            step_id = data['step_id'],
            kind = ChatStepKind(data['kind']),
            ticket = StepTicket(
                chat_id = data['chat_id'],
                phase = ChatPhase(data['phase']),
                phase_version = data['phase_version'],
            ),
            context = ChatStepContext(
                business_connection_id = data['business_connection_id'],
                username = data['username'],
                full_name = data['full_name'],
                message_datetime = datetime.fromisoformat(data['message_datetime']),
                message_text = data['message_text'],
                message_id = data['message_id'],
                remind = data['remind'],
            ),
        )
