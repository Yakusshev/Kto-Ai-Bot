from collections.abc import Mapping

from bot.core.config.ConfigError import ConfigError

TRUE_VALUE = "True"
LIST_SEPARATOR = ","
MISSING_PROBLEM = "{name}: переменная не задана"
NOT_INT_PROBLEM = "{name}: ожидается целое число, получено «{value}»"
NOT_INT_LIST_PROBLEM = (
    "{name}: ожидается список целых чисел через запятую, получено «{value}»"
)


class EnvReader:
    """
    Читает переменные окружения и копит ошибки, чтобы сообщить обо всех сразу.

    Методы require_* при ошибке возвращают пустое значение-заглушку,
    поэтому после чтения всех переменных обязательно вызывать validate().
    """

    def __init__(
        self,
        environ: Mapping[str, str],
    ):
        self._environ = environ
        self._problem_list: list[str] = []

    def optional_str(self, name: str) -> str | None:
        value = self._environ.get(name, "").strip()
        if value:
            return value
        else:
            return None

    def flag(self, name: str) -> bool:
        return self._environ.get(name) == TRUE_VALUE

    def require_str(self, name: str) -> str:
        value = self.optional_str(name)
        if value is None:
            self._problem_list.append(MISSING_PROBLEM.format(name = name))
            return ""
        else:
            return value

    def require_int(self, name: str) -> int:
        value = self.optional_str(name)
        if value is None:
            self._problem_list.append(MISSING_PROBLEM.format(name = name))
            return 0

        try:
            return int(value)
        except ValueError:
            self._problem_list.append(
                NOT_INT_PROBLEM.format(
                    name = name,
                    value = value,
                ),
            )
            return 0

    def require_int_list(self, name: str) -> list[int]:
        value = self.optional_str(name)
        if value is None:
            self._problem_list.append(MISSING_PROBLEM.format(name = name))
            return []

        try:
            return [
                int(item)
                for item in value.split(LIST_SEPARATOR)
                if item.strip()
            ]
        except ValueError:
            self._problem_list.append(
                NOT_INT_LIST_PROBLEM.format(
                    name = name,
                    value = value,
                ),
            )
            return []

    def validate(self) -> None:
        if self._problem_list:
            raise ConfigError(problem_list = list(self._problem_list))
