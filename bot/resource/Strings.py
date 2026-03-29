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
        self.locale = i18n.locale

    def sticker_not_loaded(self, emoji: object) -> str:
        return self._i18n.get('sticker-not-loaded', locale = self.locale, emoji = emoji)

    def photo_cannot_be_loaded(self) -> str:
        return self._i18n.get('photo-cannot-be-loaded', locale = self.locale)

    def photo_cannot_be_loaded_text(self, text: object) -> str:
        return self._i18n.get('photo-cannot-be-loaded-text', locale = self.locale, text = text)

    def photo_list_cannot_be_loaded(self, photo_number: object) -> str:
        return self._i18n.get('photo-list-cannot-be-loaded', locale = self.locale, photo_number = photo_number)

    def photo_list_cannot_be_loaded_text(self, photo_number: object, text: object) -> str:
        return self._i18n.get('photo-list-cannot-be-loaded-text', locale = self.locale, photo_number = photo_number, text = text)

    def voice_message_cannot_be_loaded(self) -> str:
        return self._i18n.get('voice-message-cannot-be-loaded', locale = self.locale)

    def video_message_cannot_be_loaded(self) -> str:
        return self._i18n.get('video-message-cannot-be-loaded', locale = self.locale)

    def next_text(self) -> str:
        return self._i18n.get('next-text', locale = self.locale)

    def admin_text_bot_start_success(self) -> str:
        return self._i18n.get('admin-text-bot-start-success', locale = self.locale)

    def admin_text_bot_start_failure(self) -> str:
        return self._i18n.get('admin-text-bot-start-failure', locale = self.locale)

    def admin_start_command_received(self) -> str:
        return self._i18n.get('admin-start-command-received', locale = self.locale)

    def admin_text_bot_stop_success(self) -> str:
        return self._i18n.get('admin-text-bot-stop-success', locale = self.locale)

    def admin_text_bot_stop_failure(self) -> str:
        return self._i18n.get('admin-text-bot-stop-failure', locale = self.locale)

    def admin_stop_command_received(self) -> str:
        return self._i18n.get('admin-stop-command-received', locale = self.locale)

    def you(self) -> str:
        return self._i18n.get('you', locale = self.locale)

    def forwarded_user(self, author_name: object, origin_full_name: object, origin_username: object) -> str:
        return self._i18n.get('forwarded_user', locale = self.locale, author_name = author_name, origin_full_name = origin_full_name, origin_username = origin_username)

    def forwarded_user_self(self, author_name: object) -> str:
        return self._i18n.get('forwarded_user_self', locale = self.locale, author_name = author_name)

    def forwarded_user_owner(self, author_name: object) -> str:
        return self._i18n.get('forwarded_user_owner', locale = self.locale, author_name = author_name)

    def forwarded_bot(self, author_name: object, origin_full_name: object, origin_username: object) -> str:
        return self._i18n.get('forwarded_bot', locale = self.locale, author_name = author_name, origin_full_name = origin_full_name, origin_username = origin_username)

    def forwarded_hidden_user(self, author_name: object, origin_full_name: object) -> str:
        return self._i18n.get('forwarded_hidden_user', locale = self.locale, author_name = author_name, origin_full_name = origin_full_name)

    def forwarded_chat(self, author_name: object, title: object, username: object) -> str:
        return self._i18n.get('forwarded_chat', locale = self.locale, author_name = author_name, title = title, username = username)

    def forwarded_own_chat(self, author_name: object) -> str:
        return self._i18n.get('forwarded_own_chat', locale = self.locale, author_name = author_name)

    def forwarded_channel(self, author_name: object, channel_title: object, channel_username: object) -> str:
        return self._i18n.get('forwarded_channel', locale = self.locale, author_name = author_name, channel_title = channel_title, channel_username = channel_username)

    def forwarded_own_channel(self, author_name: object) -> str:
        return self._i18n.get('forwarded_own_channel', locale = self.locale, author_name = author_name)

    def remind_instruction(self) -> str:
        return self._i18n.get('remind_instruction', locale = self.locale)

    def system_instruction(self, username: object, full_name: object, date_and_time: object) -> str:
        return self._i18n.get('system_instruction', locale = self.locale, username = username, full_name = full_name, date_and_time = date_and_time)

    def system_instruction_ignore(self) -> str:
        return self._i18n.get('system_instruction_ignore', locale = self.locale)

    def system_instruction_part_2(self, message_separator: object) -> str:
        return self._i18n.get('system_instruction_part_2', locale = self.locale, message_separator = message_separator)

    def system_instruction_part_3(self, message_separator: object) -> str:
        return self._i18n.get('system_instruction_part_3', locale = self.locale, message_separator = message_separator)

    def system_instruction_channel_lore(self) -> str:
        return self._i18n.get('system_instruction_channel_lore', locale = self.locale)
