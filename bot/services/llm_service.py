import os
import google.generativeai as genai
from abc import ABC, abstractmethod
# Добавляем cast
from typing import Union, List, Dict

from openai import OpenAI

from bot.domain.const.env_const import YANDEX_FOLDER_ID


# --- Абстрактный базовый класс ---
class LLMClient(ABC):
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Union[str, None]
    ) -> str:
        pass

YANDEX_CLOUD_MODEL = "yandexgpt-lite/latest"

class YandexOpenAICompatibleClient(OpenAI, LLMClient):

    def __init__(self, api_key: str, base_url: str):
        super().__init__(
            api_key = api_key,
            base_url = base_url,
            project = YANDEX_FOLDER_ID,
        )

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Union[str, None],
    ) -> str:
        # Динамически собираем список обычных словарей
        api_messages = []
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})

        for msg in messages:
            api_messages.append({"role": msg["role"], "content": msg["content"]})

        try:
            # Используем cast, чтобы "убедить" анализатор, что наш список имеет правильный тип
            response = self.responses.create(
                model = f"gpt://{YANDEX_FOLDER_ID}/{YANDEX_CLOUD_MODEL}",
                input = api_messages,
                temperature = 0.7,
                # previous_response_id=previous_id  # Передача контекста, если он есть
            )
            return response.output_text
        except Exception as e:
            print(
                f"Ошибка при обращении к OpenAI-совместимому API (model: {model}, url: {self.base_url}): {e}")
            return "Ошибка обращения к AI"


# --- ОБНОВЛЕННАЯ Фабрика ---
def get_llm_client() -> LLMClient:
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    if provider == "yandex":
        api_key = os.getenv("YANDEX_API_KEY")
        if not api_key:
            raise ValueError("YANDEX_API_KEY должен быть указан в .env")
        print("INFO: Using YandexGPT LLM provider (OpenAI-compatible).")
        return YandexOpenAICompatibleClient(
            api_key = api_key,
            base_url = "https://rest-assistant.api.cloud.yandex.net/v1",
        )

    else:
        raise ValueError(f"Неизвестный LLM провайдер: {provider}. Доступные: 'gemini', 'deepseek', 'yandex'.")
