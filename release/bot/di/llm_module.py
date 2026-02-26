import os

from bot.data.repository.DeepseekRepository import DeepseekRepository
from bot.domain.repository import AiRepository


def get_llm_repository() -> LLMRepository:
    provider = os.getenv("LLM_PROVIDER", "deepseek").lower()  # По умолчанию теперь deepseek

    if provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY не найден в .env")
        print("INFO: Using DeepSeek LLM provider.")
        return DeepseekRepository(api_key, base_url = "https://api.deepseek.com/v1")

    elif provider == "yandex":
        api_key = os.getenv("YANDEX_API_KEY")
        if not api_key:
            raise ValueError("YANDEX_API_KEY должен быть указан в .env")
        print("INFO: Using YandexGPT LLM provider (OpenAI-compatible).")
        return DeepseekRepository(
            api_key = api_key,
            base_url = "https://llm.api.cloud.yandex.net/openai/v1/"
        )

    elif provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY не найден в .env")
        print("INFO: Using Gemini LLM provider.")
        return GeminiRepository(api_key)

    else:
        raise ValueError(f"Неизвестный LLM провайдер: {provider}. Доступные: 'gemini', 'deepseek', 'yandex'.")
