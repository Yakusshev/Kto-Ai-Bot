import asyncio
import os
from dotenv import load_dotenv
from bot.services.gemini import generate_response
import google.generativeai as genai


async def main():
    load_dotenv()
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("Не удалось загрузить GEMINI_API_KEY. Проверьте файл .env")

    genai.configure(api_key=gemini_api_key)

    list = genai.list_models()

    for model in list:
        print(model.name)

    # try:
    #     response = await model.generate_content_async(prompt)
    #     return response.text
    # except Exception as e:
    #     print(f"Ошибка при обращении к Google Gemini: {e}")
    #     return "Ошибка обращения к AI"

    prompt = "Привет! Как дела?"
    response = await generate_response(prompt, gemini_api_key)
    print(f"Промпт: {prompt}")
    print(f"Ответ: {response}")


if __name__ == "__main__":
    asyncio.run(main())
