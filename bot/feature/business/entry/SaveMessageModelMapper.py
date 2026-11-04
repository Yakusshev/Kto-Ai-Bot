from aiogram.types import Message, MessageOriginHiddenUser, MessageOriginChat, \
    MessageOriginChannel, MessageOriginUnion

from bot.feature.business.domain.model.ForwardOriginState import ForwardOriginState, \
    ForwardOriginUserModel, ForwardOriginHiddenUserModel, ForwardOriginChatModel, \
    ForwardOriginChannelModel
from bot.feature.business.domain.model.SaveMessageModel import SaveMessageModel, \
    MessageRole
from aiogram.types import MessageOriginUser


def to_save_message_model(
    message: Message,
    content: str,
    role: MessageRole,
) -> SaveMessageModel | None:
    if content:
        return SaveMessageModel(
            chat_id = message.chat.id,
            created_at = message.date,
            message_id = message.message_id,
            role = role,
            content = content,
            event_type = 'text',
            reply_to_id = int(
                message.reply_to_message.message_id,
            ) if message.reply_to_message else None,
            text_quote = __get_quote(message = message),
            business_connection_id = str(
                message.business_connection_id,
            ) if message.business_connection_id else None,
            forward_origin = get_forward_origin(origin = message.forward_origin),
        )
    else:
        return None

def get_forward_origin(
    origin: MessageOriginUnion | None,
) -> ForwardOriginState | None:

    if isinstance(origin, MessageOriginUser):
        return ForwardOriginUserModel(
            date = origin.date,
            id = origin.sender_user.id,
            bot = origin.sender_user.is_bot,
            username = origin.sender_user.username,
            full_name = origin.sender_user.full_name,
        )
    elif isinstance(origin, MessageOriginHiddenUser):
        return ForwardOriginHiddenUserModel(
            date = origin.date,
            full_name = origin.sender_user_name,
        )
    elif isinstance(origin, MessageOriginChat):
        return ForwardOriginChatModel(
            date = origin.date,
        )
    elif isinstance(origin, MessageOriginChannel):
        username = origin.chat.username if origin.chat.username else ""
        return ForwardOriginChannelModel(
            date = origin.date,
            id = origin.chat.id,
            username = username,
            title = origin.chat.title,
            message_id = origin.message_id,
        )
    else:
        return None


def __get_quote(message: Message) -> str | None:
    if message.reply_to_message is not None and message.quote is not None:
        return str(message.quote.text)
    else:
        return None