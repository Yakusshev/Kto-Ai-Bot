from typing import List, Dict, Union

from google import generativeai as genai

from bot.domain.repository.LLMRepository import LLMRepository


class GeminiRepository(LLMRepository):
    def __init__(self, api_key: str):
        genai.configure(api_key = api_key)

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Union[str, None]
    ) -> str:
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
            return ""
