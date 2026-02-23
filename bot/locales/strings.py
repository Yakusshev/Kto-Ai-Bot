"""
Auto-generated stubs for strings.ftl
Do NOT edit manually — re-run generate_stubs.py to update.
"""

from __future__ import annotations


class Strings:
    """Типизированный доступ к ключам локализации."""

    def __init__(self, get_fn) -> None:
        # get_fn(key, **kwargs) -> str  —  любой i18n-бэкенд
        self._get = get_fn

    def sticker_not_loaded(self, *, emoji: object) -> str:
        return self._get('sticker-not-loaded', emoji = emoji)

    def empty_message(self) -> str:
        return self._get('empty-message')

    def photo_cannot_be_loaded(self, *, user: object) -> str:
        return self._get('photo-cannot-be-loaded', user = user)

    def photo_cannot_be_loaded_text(self, *, user: object, text: object) -> str:
        return self._get('photo-cannot-be-loaded-text', user = user, text = text)

    def photo_list_cannot_be_loaded(self, *, user: object, photo_number: object) -> str:
        return self._get('photo-list-cannot-be-loaded', user = user, photo_number = photo_number)

    def photo_list_cannot_be_loaded_text(self, *, user: object, photo_number: object, text: object) -> str:
        return self._get('photo-list-cannot-be-loaded-text', user = user, photo_number = photo_number, text = text)

    def next_text(self) -> str:
        return self._get('next-text')
