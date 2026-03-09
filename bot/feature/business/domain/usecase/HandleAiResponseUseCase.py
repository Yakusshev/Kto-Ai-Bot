import re
from random import random
from typing import List
from venv import logger


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

        return self.split_messages(response = response)

    @staticmethod
    def split_messages(
        response: str,
    ) -> List[str]:

        pattern = fr'\n|\n\n|{HandleAiResponseUseCase.NEXT_MESSAGE_TAG_REGEX}'

        response_no_brackets = HandleAiResponseUseCase\
            .replace_brackets_except_next(response)

        response_no_zero_no_tire = re\
            .sub(r'\b0\b', '', response_no_brackets)\
            .replace('—', '-')\
            .replace('–', '-')
        response_no_space = re\
            .sub(r' +', ' ', response_no_zero_no_tire)

        lines: list[str] = re.split(pattern, response_no_space)

        logger.info(f'GenerateAiResponseUseCase.split_messages lines = {lines}')

        if not lines:
            logger.warning(
                f'GenerateAiResponseUseCase.split_messages: empty lines; '
                f'response = {response}',
            )
            return []

        result = []
        current = lines[0]

        double_message = False

        for i, line in enumerate(lines[1:]):
            if line[i - 1] != line:
                if random() < 0.75:
                    result.append(current)
                    current = line
                else:
                    current += '\n' + line
            else:
                double_message = True

        if double_message:
            logger.info(f"DOUBLE_MESSAGE: ${lines}")

        result.append(current.strip())

        return result

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
