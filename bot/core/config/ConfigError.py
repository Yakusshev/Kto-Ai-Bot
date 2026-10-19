class ConfigError(Exception):
    """Окружение не содержит обязательных переменных или содержит некорректные значения."""

    def __init__(
        self,
        problem_list: list[str],
    ):
        self.problem_list = problem_list
        lines = "\n".join(f"  - {problem}" for problem in problem_list)
        super().__init__(f"Некорректная конфигурация окружения:\n{lines}")
