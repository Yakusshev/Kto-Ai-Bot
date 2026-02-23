"""
Auto-generated stubs for strings.ftl
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

    def photo_cannot_be_loaded(self, *, user: object) -> str:
        return self._i18n.get('photo-cannot-be-loaded', user=user)

    def photo_cannot_be_loaded_text(self, *, user: object, text: object) -> str:
        return self._i18n.get('photo-cannot-be-loaded-text', user=user, text=text)

    def photo_list_cannot_be_loaded(self, *, user: object, photo_number: object) -> str:
        return self._i18n.get('photo-list-cannot-be-loaded', user=user, photo_number=photo_number)

    def photo_list_cannot_be_loaded_text(self, *, user: object, photo_number: object, text: object) -> str:
        return self._i18n.get('photo-list-cannot-be-loaded-text', user=user, photo_number=photo_number, text=text)

    def photo_list_cannot_be_loaded_text(self, *, user: object, photo_number: object, text: object) -> str:
        return self._i18n.get('photo-list-cannot-be-loaded-text', user=user, photo_number=photo_number, text=text)

    def next_text(self) -> str:
        return self._i18n.get('next-text')
