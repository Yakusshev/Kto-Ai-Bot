from datetime import datetime

from aiogram.types import ChatFullInfo

from bot.feature.business.domain.model.UserModel import UserModel, BirthdateModel


def to_user_model(
    chat: ChatFullInfo,
) -> UserModel:
    birthdate_dt = None
    if chat.birthdate:
        birthdate_dt = BirthdateModel(
            year = chat.birthdate.year if chat.birthdate.year else None,
            month = chat.birthdate.month,
            day = chat.birthdate.day,
        )

    channel_id = None
    channel_title = None
    channel_username = None

    if chat.personal_chat:
        channel_id = chat.personal_chat.id
        channel_title = chat.personal_chat.title
        channel_username = chat.personal_chat.username

    return UserModel(
        id = chat.id,
        username = chat.username,
        # TODO
        first_name = chat.first_name,
        # Защита от None, если поле обязательное
        last_name = chat.last_name,
        bio = chat.bio,
        birthdate = birthdate_dt,
        # Поле business_connection_id обычно приходит из Update, а не из ChatFullInfo
        business_connection_id = None,
        update_date = datetime.now(),  # Ставим текущее время как время обновления
        channel_title = channel_title,
        channel_username = channel_username,
        channel_id = channel_id,
    )
