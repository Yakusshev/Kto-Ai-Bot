import random

from bot.feature.business.domain.repository.DelayedTaskQueue import MAX_DELAY_SECONDS

SEE_MESSAGE_RANGE = (10, 30)  # сек до «прочитал»
MIN_READ_SECONDS = 2.0
WORDS_PER_SECOND = 1.5
WRITE_SPEED_RANGE = (2, 6)  # символов в секунду
MIN_WRITE_SECONDS = 1.5


class HumanDelays:
    """
    Паузы «как у человека» между шагами ответа.

    is_instant (DEBUG_MODE_TYPING) - все паузы нулевые.
    Паузы между шагами уходят в delay_seconds очереди, поэтому не превышают
    её предел MAX_DELAY_SECONDS (иначе очередь отказала бы или пауза была бы обрезана).
    """

    def __init__(
        self,
        is_instant: bool,
    ):
        self._is_instant = is_instant

    def see_message(self) -> float:
        """Пауза до «прочитал»."""
        if self._is_instant:
            return 0.0
        return random.uniform(a = SEE_MESSAGE_RANGE[0], b = SEE_MESSAGE_RANGE[1])

    def start_typing(
        self,
        message_text: str,
    ) -> float:
        """Пауза до «печатает...»: время прочитать сообщение, но не больше предела очереди."""
        if self._is_instant:
            return 0.0
        read_time = max(MIN_READ_SECONDS, len(message_text.split()) / WORDS_PER_SECOND)
        return min(read_time, float(MAX_DELAY_SECONDS))

    def write_message(
        self,
        text: str,
    ) -> float:
        """Пауза перед отправкой одного сообщения ответа (выполняется внутри шага)."""
        if self._is_instant:
            return 0.0
        write_time = len(text) / random.uniform(
            a = WRITE_SPEED_RANGE[0],
            b = WRITE_SPEED_RANGE[1],
        )
        return max(write_time, MIN_WRITE_SECONDS)
