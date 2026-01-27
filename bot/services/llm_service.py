import os
import aiohttp
import openai
import google.generativeai as genai
from abc import ABC, abstractmethod
from typing import Union, List, Dict

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
        # Gemini не понимает списка ролей, поэтому мы преобразуем все в единый промпт-строку.
        prompt_parts = []
        if system_prompt:
            prompt_parts.append(system_prompt)
        
        for msg in messages:
            # Gemini лучше работает с форматом "роль: текст"
            prompt_parts.append(f"{msg['role']}: {msg['content']}")
        
        full_prompt = "\\n".join(prompt_parts)

        try:
            genai_model = genai.GenerativeModel(model)
            response = await genai_model.generate_content_async(full_prompt)
            return response.text
        except Exception as e:
            print(f"Ошибка при обращении к Google Gemini (model: {model}): {e}")
            return "Ошибка обращения к AI"

# --- Реализация для DeepSeek и YandexGPT (OpenAI-совместимые) ---
class OpenAICompatibleClient(LLMClient):
    def __init__(self, api_key: str, base_url: str):
        self.async_client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def generate_response(self, messages: List[Dict[str, str]], model: str, system_prompt: Union[str, None]) -> str:
        # Создаем копию, чтобы не изменять оригинальный список
        api_messages = list(messages)
        if system_prompt:
            # Вставляем системный промпт в начало
            api_messages.insert(0, {"role": "system", "content": system_prompt})
        
        try:
            response = await self.async_client.chat.completions.create(
                model=model,
                messages=api_messages,
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Ошибка при обращении к OpenAI-совместимому API (model: {model}): {e}")
            return "Ошибка обращения к AI"

# --- НОВАЯ РЕАЛИЗАЦИЯ для YandexGPT ---
class YandexGPTClient(LLMClient):
    def __init__(self, api_key: str, folder_id: str):
        self.api_key = api_key
        self.folder_id = folder_id
        self.endpoint = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    async def generate_response(self, messages: List[Dict[str, str]], model: str, system_prompt: Union[str, None]) -> str:
        headers = {"Authorization": f"Api-Key {self.api_key}", "Content-Type": "application/json"}
        
        api_messages = list(messages)
        if system_prompt:
            api_messages.insert(0, {"role": "system", "content": system_prompt})

        payload = {
            "modelUri": f"gpt://{self.folder_id}/{model}",
            "completionOptions": {"stream": False, "temperature": 0.6, "maxTokens": "2000"},
            "messages": api_messages
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.endpoint, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['result']['alternatives'][0]['message']['text']
                    else:
                        error_text = await response.text()
                        print(f"Ошибка при обращении к YandexGPT. Статус: {response.status}, Ответ: {error_text}")
                        return "Ошибка обращения к AI"
        except Exception as e:
            print(f"Исключение при обращении к YandexGPT: {e}")
            return "Ошибка обращения к AI"

# --- ОБНОВЛЕННАЯ Фабрика ---
def get_llm_client() -> LLMClient:
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider == "yandex":
        api_key = os.getenv("YANDEX_API_KEY")
        folder_id = os.getenv("YANDEX_FOLDER_ID")
        if not api_key or not folder_id:
            raise ValueError("YANDEX_API_KEY и YANDEX_FOLDER_ID должны быть указаны в .env")
        print("INFO: Using YandexGPT LLM provider.")
        return YandexGPTClient(api_key, folder_id)

    elif provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY не найден в .env")
        print("INFO: Using DeepSeek LLM provider.")
        # Используем универсальный OpenAI-совместимый клиент
        return OpenAICompatibleClient(api_key, base_url="https://api.deepseek.com/v1")
    
    elif provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY не найден в .env")
        print("INFO: Using Gemini LLM provider.")
        return GeminiClient(api_key)
        
    else:
        raise ValueError(f"Неизвестный LLM провайдер: {provider}. Доступные: 'gemini', 'deepseek', 'yandex'.")
