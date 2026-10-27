import pytest

from bot.core.config.ConfigError import ConfigError
from bot.core.config.EnvReader import EnvReader


def create_reader(
    environ: dict[str, str],
) -> EnvReader:
    return EnvReader(environ = environ)


def collect_problem_list(
    reader: EnvReader,
) -> list[str]:
    with pytest.raises(ConfigError) as error_info:
        reader.validate()
    return error_info.value.problem_list


class TestEnvReader:

    # --- require_int ---

    def test_when_int_is_set_expect_parsed_value(self):
        # Arrange
        reader = create_reader(environ = {"OWN_CHAT_ID": "-100123"})
        expected = -100123

        # Act
        actual = reader.require_int("OWN_CHAT_ID")

        # Assert
        assert actual == expected
        reader.validate()

    def test_when_int_is_missing_expect_error_with_variable_name(self):
        # Arrange
        reader = create_reader(environ = {})
        reader.require_int("OWN_CHAT_ID")
        expected = ["OWN_CHAT_ID: переменная не задана"]

        # Act
        actual = collect_problem_list(reader = reader)

        # Assert
        assert actual == expected

    def test_when_int_is_blank_expect_error_with_variable_name(self):
        # Arrange
        reader = create_reader(environ = {"OWN_CHAT_ID": "   "})
        reader.require_int("OWN_CHAT_ID")
        expected = ["OWN_CHAT_ID: переменная не задана"]

        # Act
        actual = collect_problem_list(reader = reader)

        # Assert
        assert actual == expected

    def test_when_int_is_not_number_expect_error_with_value(self):
        # Arrange
        reader = create_reader(environ = {"OWN_CHAT_ID": "abc"})
        reader.require_int("OWN_CHAT_ID")
        expected = ["OWN_CHAT_ID: ожидается целое число, получено «abc»"]

        # Act
        actual = collect_problem_list(reader = reader)

        # Assert
        assert actual == expected

    # --- require_int_list ---

    def test_when_int_list_is_set_expect_parsed_list(self):
        # Arrange
        reader = create_reader(environ = {"ADMIN_ID_LIST": "1, 2,3,"})
        expected = [1, 2, 3]

        # Act
        actual = reader.require_int_list("ADMIN_ID_LIST")

        # Assert
        assert actual == expected
        reader.validate()

    def test_when_int_list_is_missing_expect_error(self):
        # Arrange
        reader = create_reader(environ = {})
        reader.require_int_list("ADMIN_ID_LIST")
        expected = ["ADMIN_ID_LIST: переменная не задана"]

        # Act
        actual = collect_problem_list(reader = reader)

        # Assert
        assert actual == expected

    def test_when_int_list_has_not_number_expect_error_with_value(self):
        # Arrange
        reader = create_reader(environ = {"ADMIN_ID_LIST": "1,x"})
        reader.require_int_list("ADMIN_ID_LIST")
        expected = [
            "ADMIN_ID_LIST: ожидается список целых чисел через запятую, получено «1,x»",
        ]

        # Act
        actual = collect_problem_list(reader = reader)

        # Assert
        assert actual == expected

    # --- require_str / optional_str / flag ---

    def test_when_str_is_set_expect_stripped_value(self):
        # Arrange
        reader = create_reader(environ = {"YDB_PATH": " /ru/db "})
        expected = "/ru/db"

        # Act
        actual = reader.require_str("YDB_PATH")

        # Assert
        assert actual == expected
        reader.validate()

    def test_when_optional_str_is_missing_expect_none_without_error(self):
        # Arrange
        reader = create_reader(environ = {})

        # Act
        actual = reader.optional_str("YDB_AUTH_KEY_FILE")

        # Assert
        assert actual is None
        reader.validate()

    @pytest.mark.parametrize(
        argnames = ("raw_value", "expected"),
        argvalues = [
            ("True", True),
            ("False", False),
            ("true", False),
            (None, False),
        ],
    )
    def test_when_flag_is_read_expect_true_only_for_exact_true(
        self,
        raw_value: str | None,
        expected: bool,
    ):
        # Arrange
        environ = {} if raw_value is None else {"DEBUG_MODE_TOKEN": raw_value}
        reader = create_reader(environ = environ)

        # Act
        actual = reader.flag("DEBUG_MODE_TOKEN")

        # Assert
        assert actual == expected

    # --- validate ---

    def test_when_several_problems_expect_all_listed_in_one_error(self):
        # Arrange
        reader = create_reader(environ = {"OWN_CHANNEL_ID": "abc"})
        reader.require_int("OWN_CHANNEL_ID")
        reader.require_int("OWN_CHAT_ID")
        reader.require_str("YDB_PATH")
        expected = (
            "Некорректная конфигурация окружения:\n"
            "  - OWN_CHANNEL_ID: ожидается целое число, получено «abc»\n"
            "  - OWN_CHAT_ID: переменная не задана\n"
            "  - YDB_PATH: переменная не задана"
        )

        # Act
        with pytest.raises(ConfigError) as error_info:
            reader.validate()
        actual = str(error_info.value)

        # Assert
        assert actual == expected

    def test_when_all_values_valid_expect_no_error(self):
        # Arrange
        reader = create_reader(
            environ = {
                "OWN_CHAT_ID": "1",
                "ADMIN_ID_LIST": "2",
                "YDB_PATH": "/db",
            },
        )
        reader.require_int("OWN_CHAT_ID")
        reader.require_int_list("ADMIN_ID_LIST")
        reader.require_str("YDB_PATH")

        # Act
        reader.validate()

        # Assert: validate не бросил исключение


class TestOptionalChoice:

    def test_when_not_set_expect_default_without_error(self):
        reader = EnvReader(environ = {})

        assert reader.optional_choice("MODE", allowed = ("memory", "sqs"), default = "memory") == "memory"
        reader.validate()

    def test_when_allowed_value_expect_value(self):
        reader = EnvReader(environ = {"MODE": " sqs "})

        assert reader.optional_choice("MODE", allowed = ("memory", "sqs"), default = "memory") == "sqs"
        reader.validate()

    def test_when_unknown_value_expect_config_error_with_allowed_list(self):
        reader = EnvReader(environ = {"MODE": "kafka"})

        reader.optional_choice("MODE", allowed = ("memory", "sqs"), default = "memory")

        with pytest.raises(ConfigError) as error:
            reader.validate()
        assert "memory, sqs" in str(error.value)
        assert "kafka" in str(error.value)

