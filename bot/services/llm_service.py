from abc import ABC, abstractmethod
# Добавляем cast
from typing import Union, List, Dict

from openai import OpenAI

from bot.domain.const.env_const import YANDEX_FOLDER_ID, YANDEX_API_KEY


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

    def __init__(self):
        super().__init__(
            api_key = YANDEX_API_KEY,
            base_url = "https://ai.api.cloud.yandex.net/v1",
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
            api_messages.append(
                {
                    "role": "system",
                    "content": system_prompt
                }
            )

        for msg in messages:
            if msg['role'] not in ['user', 'assistant']:
                print(f"WARNING: Invalid role {msg['role']} in history!")
            else:
                api_messages.append(
                    {
                        "role": msg["role"],
                        "content": msg["content"],
                    }
                )

        print('generate_response: api_messages\n', api_messages)
        try:
            response = self.responses.create(
                model = model,
                input = api_messages,
                temperature = 0.7,
                max_output_tokens = 100,
            )
            return response.output[0].content[0].text
        except Exception as e:
            print(f"Ошибка при обращении к OpenAI-совместимому API (model: {model}, url: {self.base_url}): {e}")
            return "Ошибка обращения к AI"


# --- ОБНОВЛЕННАЯ Фабрика ---
def get_llm_client() -> LLMClient:
    return YandexOpenAICompatibleClient()
