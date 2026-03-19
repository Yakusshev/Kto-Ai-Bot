import pytest
from unittest.mock import patch

from bot.feature.business.domain.usecase.HandleAiResponseUseCase import \
    HandleAiResponseUseCase

RANDOM = 'bot.feature.business.domain.usecase.HandleAiResponseUseCase.random'


class TestHandleAiResponseUseCase:

    @pytest.fixture
    def use_case(self) -> HandleAiResponseUseCase:
        return HandleAiResponseUseCase()

    # --- Базовые проверки ---

    @pytest.mark.asyncio
    async def test_when_empty_response_expect_empty_list(
        self,
        use_case: HandleAiResponseUseCase,
    ):
        raw_response = ""
        with pytest.raises(Exception):
            await use_case.invoke(raw_response)


    @pytest.mark.asyncio
    async def test_when_single_line_expect_single_element_list(
        self,
        use_case: HandleAiResponseUseCase,
    ):
        expected = ["Обычный текст"]

        raw_response = "Обычный текст"
        actual = await use_case.invoke(raw_response)

        assert actual == expected

    # --- Проверка логики склеивания/разделения сообщений (random) ---

    @pytest.mark.asyncio
    async def test_when_newlines_and_random_less_than_threshold_expect_split_messages(
        self,
        use_case: HandleAiResponseUseCase,
    ):
        expected = ["Первое", "Второе"]

        raw_response = "Первое\nВторое"
        with patch(target = RANDOM, return_value = 0.0):
            actual = await use_case.invoke(raw_response)

        assert actual == expected

    @pytest.mark.asyncio
    async def test_when_newlines_and_random_greater_than_threshold_expect_joined_message(
        self,
        use_case: HandleAiResponseUseCase,
    ):
        expected = ["Первое\nВторое"]

        raw_response = "Первое\nВторое"
        with patch(target = RANDOM, return_value = 0.8):
            actual = await use_case.invoke(raw_response)

        assert actual == expected

    # --- Проверка работы с тегом [next] и скобками ---

    @pytest.mark.asyncio
    async def test_when_next_tag_present_expect_split_by_tag(
        self,
        use_case: HandleAiResponseUseCase,
    ):
        expected = ["Часть 1", "Часть 2"]

        raw_response = "Часть 1[next]Часть 2"
        with patch(target = RANDOM, return_value = 0.0):
            actual = await use_case.invoke(raw_response)

        assert actual == expected

    @pytest.mark.asyncio
    async def test_when_other_brackets_present_expect_brackets_replaced_with_space(
        self,
        use_case: HandleAiResponseUseCase,
    ):
        expected = ["Действие завершено"]

        raw_response = "Действие[вздыхает] завершено"
        actual = await use_case.invoke(raw_response)

        assert actual == expected

    # --- Проверка очистки текста (нули, тире, пробелы) ---

    @pytest.mark.asyncio
    async def test_when_standalone_zero_present_expect_zero_removed(
        self,
        use_case: HandleAiResponseUseCase,
    ):
        expected = ["У меня яблок"]

        raw_response = "У меня 0 яблок"
        actual = await use_case.invoke(raw_response)

        assert actual == expected

    @pytest.mark.asyncio
    async def test_when_zero_inside_word_expect_zero_kept(
        self,
        use_case: HandleAiResponseUseCase,
    ):
        expected = ["Счетчик 100 и v0"]

        raw_response = "Счетчик 100 и v0"
        actual = await use_case.invoke(raw_response)

        assert actual == expected

    @pytest.mark.asyncio
    async def test_when_multiple_spaces_present_expect_single_space(
        self,
        use_case: HandleAiResponseUseCase,
    ):
        expected = ["Много пробелов"]

        raw_response = "Много      пробелов"
        actual = await use_case.invoke(raw_response)

        assert actual == expected

    @pytest.mark.asyncio
    async def test_when_different_dashes_present_expect_regular_hyphen(
        self,
        use_case: HandleAiResponseUseCase,
    ):
        expected = ["один - два - три"]

        raw_response = "один — два – три"
        actual = await use_case.invoke(raw_response)

        assert actual == expected

    # --- Проверка предотвращения дубликатов ---

    @pytest.mark.asyncio
    async def test_when_consecutive_duplicate_lines_expect_duplicates_removed(
        self,
        use_case: HandleAiResponseUseCase,
    ):
        expected = ["Повтор"]

        raw_response = "Повтор\nПовтор\nПовтор"
        with patch(target = RANDOM, return_value = 0.0):
            actual = await use_case.invoke(raw_response)

        assert actual == expected

    @pytest.mark.asyncio
    async def test_when_non_consecutive_duplicate_lines_expect_second_occurrence_ignored(
        self,
        use_case: HandleAiResponseUseCase,
    ):
        expected = ["Раз", "Два"]

        raw_response = "Раз\nДва\nРаз"
        with patch(target = RANDOM, return_value = 0.0):
            actual = await use_case.invoke(raw_response)

        assert actual == expected

    # --- Проверка обрезки зацикливаний (fix_looping_response_advanced) ---

    @pytest.mark.asyncio
    async def test_when_char_loops_expect_truncated_text(
        self,
        use_case: HandleAiResponseUseCase,
    ):
        expected = ["Стой"]

        # 'а' повторяется больше 7 раз
        raw_response = "Стой аааааааааа"
        actual = await use_case.invoke(raw_response)

        assert actual == expected

    @pytest.mark.asyncio
    async def test_when_word_loops_expect_truncated_text(
        self,
        use_case: HandleAiResponseUseCase,
    ):
        expected = ["Ответ:"]

        # 'да ' повторяется больше 9 раз
        raw_response = "Ответ: да да да да да да да да да да да да"
        actual = await use_case.invoke(raw_response)

        assert actual == expected

    @pytest.mark.asyncio
    async def test_when_phrase_loops_expect_truncated_text(
        self,
        use_case: HandleAiResponseUseCase,
    ):
        expected = ["Пока."]

        # Фраза повторяется больше 3 раз
        raw_response = "Пока. я иду домой я иду домой я иду домой я иду домой я иду домой"
        actual = await use_case.invoke(raw_response)

        assert actual == expected

    # --- Проверка работы с Unicode и экранированием (clean_unicode) ---

    @pytest.mark.asyncio
    async def test_when_unicode_escaped_string_expect_decoded_string(
        self,
        use_case: HandleAiResponseUseCase,
    ):
        expected = ["Test"]

        # Латиница проходит try блок без исключений
        raw_response = "\\u0054\\u0065\\u0073\\u0074"
        actual = await use_case.invoke(raw_response)

        assert actual == expected

    @pytest.mark.asyncio
    async def test_when_cyrillic_with_escaped_newline_expect_fallback_decode(
        self,
        use_case: HandleAiResponseUseCase,
    ):
        expected = ["Привет", "Мир"]

        # Кириллица вызывает ошибку при кодировании в latin-1, срабатывает блок except
        raw_response = "Привет\\nМир"
        with patch(target = RANDOM, return_value = 0.0):
            actual = await use_case.invoke(raw_response)

        assert actual == expected

    @pytest.mark.asyncio
    async def test_when_cyrillic_with_escaped_tab_expect_fallback_decode(
        self,
        use_case: HandleAiResponseUseCase,
    ):
        expected = ["Колонка 1\tКолонка 2"]

        raw_response = "Колонка 1\\tКолонка 2"
        actual = await use_case.invoke(raw_response)

        assert actual == expected
