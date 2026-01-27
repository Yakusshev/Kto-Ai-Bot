import os
import openai
import google.generativeai as genai
from abc import ABC, abstractmethod
# Добавляем cast
from typing import Union, List, Dict, cast
# Импортируем тип для кастинга
from openai.types.chat import ChatCompletionMessageParam

# --- Абстрактный базовый класс ---
class LLMClient(ABC):
    @abstractmethod
    async def generate_response(self, messages: List[Dict[str, str]], model: str, system_prompt: Union[str, None]) -> str:
        pass

# --- Реализация для Gemini ---
class GeminiClient(LLMClient):
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)

    async def generate_response(self, messages: List[Dict[str, str]], model: str, system_prompt: Union[str, None]) -> str:
        prompt_parts = []
        if system_prompt:
            prompt_parts.append(system_prompt)
        
        for msg in messages:
            prompt_parts.append(f"{msg['role']}: {msg['content']}")
        
        full_prompt = "\n".join(prompt_parts)

        try:
            genai_model = genai.GenerativeModel(model)
            response = await genai_model.generate_content_async(full_prompt)
            return response.text
        except Exception as e:
            print(f"Ошибка при обращении к Google Gemini (model: {model}): {e}")
            return "Ошибка обращения к AI"

# --- Универсальный клиент для OpenAI-совместимых API (DeepSeek, YandexGPT) ---
class OpenAICompatibleClient(LLMClient):
    def __init__(self, api_key: str, base_url: str):
        self.async_client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def generate_response(self, messages: List[Dict[str, str]], model: str, system_prompt: Union[str, None]) -> str:
        # Динамически собираем список обычных словарей
        api_messages = []
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        
        for msg in messages:
            api_messages.append({"role": msg["role"], "content": msg["content"]})

        try:
            # Используем cast, чтобы "убедить" анализатор, что наш список имеет правильный тип
            response = await self.async_client.chat.completions.create(
                model=model,
                messages=cast(List[ChatCompletionMessageParam], api_messages),
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Ошибка при обращении к OpenAI-совместимому API (model: {model}, url: {self.async_client.base_url}): {e}")
            return "Ошибка обращения к AI"

# --- ОБНОВЛЕННАЯ Фабрика ---
def get_llm_client() -> LLMClient:
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider == "yandex":
        api_key = os.getenv("YANDEX_API_KEY")
        if not api_key:
            raise ValueError("YANDEX_API_KEY должен быть указан в .env")
        print("INFO: Using YandexGPT LLM provider (OpenAI-compatible).")
        return OpenAICompatibleClient(api_key, base_url="https://llm.api.cloud.yandex.net/openai/v1/")

    elif provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY не найден в .env")
        print("INFO: Using DeepSeek LLM provider.")
        return OpenAICompatibleClient(api_key, base_url="https://api.deepseek.com/v1")
    
    elif provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY не найден в .env")
        print("INFO: Using Gemini LLM provider.")
        return GeminiClient(api_key)
        
    else:
        raise ValueError(f"Неизвестный LLM провайдер: {provider}. Доступные: 'gemini', 'deepseek', 'yandex'.")
