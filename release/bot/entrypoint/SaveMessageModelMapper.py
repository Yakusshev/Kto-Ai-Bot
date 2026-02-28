from aiogram.types import Message

from bot.domain.model.SaveMessageModel import SaveMessageModel, MessageRole


def to_save_message_model(
    message: Message,
    content: str,
    role: MessageRole,
    empty_message: str,
) -> SaveMessageModel:
    return SaveMessageModel(
        chat_id = message.chat.id,
        created_at = message.date,
        message_id = message.message_id,
        role = role,
        content = empty_message if not content else content,
        event_type = 'text',
        reply_to_id = int(message.reply_to_message.message_id) if message.reply_to_message else None,
        text_quote = __get_quote(message = message),
        business_connection_id = str(message.business_connection_id) if message.business_connection_id else None,
    )

def __get_quote(message: Message) -> str | None:
    if message.reply_to_message is not None and message.quote is not None:
        return str(message.quote.text)
    else:
        return None