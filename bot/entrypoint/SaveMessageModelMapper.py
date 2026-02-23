from aiogram.types import Message

from bot.domain.model.SaveMessageModel import SaveMessageModel


def to_save_message_model(
    message: Message,
    content: str,
    role: str,
) -> SaveMessageModel:
    return SaveMessageModel(
        chat_id = message.chat.id,
        created_at = message.date,
        message_id = message.message_id,
        role = role,
        content = content,
        event_type = 'text',
        reply_to_id = int(message.reply_to_message.message_id) if message.reply_to_message else None,
        text_quote = str(message.quote.text) if message.quote else None,
        business_connection_id = str(message.business_connection_id) if message.business_connection_id else None,
    )