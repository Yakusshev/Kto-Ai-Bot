"""
Auto-generated stubs for messages.ftl
Do NOT edit manually — re-run generate_stubs.py to update.
"""

from __future__ import annotations

from aiogram_i18n import I18nContext


class Strings:
    """Типизированный доступ к ключам локализации через I18nContext."""

    def __init__(self, i18n: I18nContext) -> None:
        self._i18n = i18n

    def sticker_not_loaded(self, *, emoji: object) -> str:
        return self._i18n.get('sticker-not-loaded', emoji=emoji)

    def empty_message(self) -> str:
        return self._i18n.get('empty-message')

    def photo_cannot_be_loaded(self) -> str:
        return self._i18n.get('photo-cannot-be-loaded')

    def photo_cannot_be_loaded_text(self, *, text: object) -> str:
        return self._i18n.get('photo-cannot-be-loaded-text', text=text)

    def photo_list_cannot_be_loaded(self, *, photo_number: object) -> str:
        return self._i18n.get('photo-list-cannot-be-loaded', photo_number=photo_number)

    def photo_list_cannot_be_loaded_text(self, *, photo_number: object, text: object) -> str:
        return self._i18n.get('photo-list-cannot-be-loaded-text', photo_number=photo_number, text=text)

    def voice_message_cannot_be_loaded(self) -> str:
        return self._i18n.get('voice-message-cannot-be-loaded')

    def video_message_cannot_be_loaded(self) -> str:
        return self._i18n.get('video-message-cannot-be-loaded')

    def next_text(self) -> str:
        return self._i18n.get('next-text')

    def admin_text_bot_start_success(self) -> str:
        return self._i18n.get('admin-text-bot-start-success')

    def admin_text_bot_start_failure(self) -> str:
        return self._i18n.get('admin-text-bot-start-failure')

    def admin_text_bot_stop_success(self) -> str:
        return self._i18n.get('admin-text-bot-stop-success')

    def admin_text_bot_stop_failure(self) -> str:
        return self._i18n.get('admin-text-bot-stop-failure')

    def you(self) -> str:
        return self._i18n.get('you')

    def forwarded_user(self, *, author_name: object, origin_full_name: object, origin_username: object) -> str:
        return self._i18n.get('forwarded_user', author_name=author_name, origin_full_name=origin_full_name, origin_username=origin_username)

    def forwarded_user_self(self, *, author_name: object) -> str:
        return self._i18n.get('forwarded_user_self', author_name=author_name)

    def forwarded_user_owner(self, *, author_name: object) -> str:
        return self._i18n.get('forwarded_user_owner', author_name=author_name)

    def forwarded_bot(self, *, author_name: object, origin_full_name: object, origin_username: object) -> str:
        return self._i18n.get('forwarded_bot', author_name=author_name, origin_full_name=origin_full_name, origin_username=origin_username)

    def forwarded_hidden_user(self, *, author_name: object, origin_full_name: object) -> str:
        return self._i18n.get('forwarded_hidden_user', author_name=author_name, origin_full_name=origin_full_name)

    def forwarded_chat(self, *, author_name: object, title: object, username: object) -> str:
        return self._i18n.get('forwarded_chat', author_name=author_name, title=title, username=username)

    def forwarded_own_chat(self, *, author_name: object) -> str:
        return self._i18n.get('forwarded_own_chat', author_name=author_name)

    def forwarded_channel(self, *, author_name: object, channel_title: object, channel_username: object) -> str:
        return self._i18n.get('forwarded_channel', author_name=author_name, channel_title=channel_title, channel_username=channel_username)

    def forwarded_own_channel(self, *, author_name: object) -> str:
        return self._i18n.get('forwarded_own_channel', author_name=author_name)

    def system_instruction(self, *, username: object, full_name: object, date_and_time: object) -> str:
        return self._i18n.get('system_instruction', username=username, full_name=full_name, date_and_time=date_and_time)

    def system_instruction_part_2(self, *, message_separator: object) -> str:
        return self._i18n.get('system_instruction_part_2', message_separator=message_separator)

    def system_instruction_part_3(self, *, message_separator: object) -> str:
        return self._i18n.get('system_instruction_part_3', message_separator=message_separator)
