import re
from random import random
from typing import List

from bot.util.log_util import get_logger


class HandleAiResponseUseCase:
    NEXT_MESSAGE_TAG_REGEX = r'\[next\]'

    def __init__(
        self,
    ):
        pass

    async def invoke(
        self,
        response: str,
    ) -> List[str]:

        logger.info(f'invoke: {response}')

        return self.split_messages(response = response)

    @staticmethod
    def split_messages(
        response: str,
    ) -> List[str]:

        response_no_brackets = HandleAiResponseUseCase\
            .replace_brackets_except_next(response)

        response_no_unicode = HandleAiResponseUseCase\
            .clean_unicode(response_no_brackets)

        response_no_zero_no_tire = re\
            .sub(r'\b0\b', '', response_no_unicode)\
            .replace('—', '-')\
            .replace('–', '-')
        response_no_space = re\
            .sub(r' +', ' ', response_no_zero_no_tire)

        response_no_repeat = HandleAiResponseUseCase \
            .fix_looping_response_advanced(text = response_no_space)

        pattern = fr'\n+|{HandleAiResponseUseCase.NEXT_MESSAGE_TAG_REGEX}'
        lines: list[str] = re.split(pattern, response_no_repeat)

        logger.info(f'split_messages lines = {lines}')

        if not lines:
            logger.warning(
                f'split_messages: empty lines; '
                f'response = {response}',
            )
            return []

        result: list[str] = []
        current = lines[0]

        double_message = False

        for i, line in enumerate(lines[1:]):

            logger.debug(f"i = {i}, line = {line}, lines[i] = {lines[i]}")

            repeat = HandleAiResponseUseCase\
                .find(message_list = result, match = line)

            if lines[i] != line and not repeat:
                if random() < 0.75:
                    result.append(current)
                    current = line
                else:
                    current += '\n' + line
            else:
                double_message = lines[i] == line

        if double_message:
            logger.info(f"DOUBLE_MESSAGE: ${lines}")

        result.append(current.strip())

        return result

    @staticmethod
    def find(message_list: List[str], match: str) -> bool:
        for message in message_list:
            logger.debug(f"find: message = {message}, match = {match}")
            if match == message:
                return True
        return False

    @staticmethod
    def replace_brackets_except_next(text: str) -> str:
        """
        Заменяет все вхождения вида [что-то] на пробел,
        за исключением точного тега [next], который сохраняется.
        """
        # Шаблон: открывающая скобка, затем любое количество символов, не содержащих ']',
        # затем закрывающая скобка. Это покрывает большинство простых случаев без вложенности.
        pattern = r'\[[^\]]*\]'

        def replacer(match):
            token = match.group(0)
            # Если это точно тег [next], оставляем как есть
            if token == '[next]':
                return token
            # Иначе заменяем на пробел
            return ' '

        return re.sub(pattern, replacer, text)

    @staticmethod
    def fix_looping_response_advanced(
        text: str,
    ) -> str:

        logger.info(f'fix_looping_response_advanced input = {text}')

        threshold_char: int = 7
        threshold_word: int = 9
        threshold_phrase: int = 3

        if not text:
            return text

        # Паттерны для разных видов зацикливания с единым порогом
        patterns = [
            # Повторение одного символа (например, "оооооо")
            (r'(.)\1{' + str(threshold_char) + r',}', 'char'),
            # Повторение слова/слога (2-10 символов)
            (r'(.{2,10})\1{' + str(threshold_word) + r',}', 'word'),
            # \1{4,} значит 5+ повторений
            # Повторение фразы (5-30 символов)
            (r'(.{5,30})\1{' + str(threshold_phrase) + r',}', 'phrase')
            # чуть меньше порог для длинных фраз
        ]

        for pattern, _ in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                # Обрезаем до начала зацикливания
                return text[:match.start()].strip()

        output = text.strip()

        logger.info(f'fix_looping_response_advanced output = {output}')

        return output

    @staticmethod
    def clean_unicode(raw_text: str) -> str:
        try:
            return raw_text.encode('latin-1')\
                .decode(encoding = 'unicode_escape', errors = 'ignore')
        except Exception as e:
            logger.error(e)
            return raw_text

logger = get_logger(HandleAiResponseUseCase.__name__)