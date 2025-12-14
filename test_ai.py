import asyncio
import os
from dotenv import load_dotenv
from bot.services.gemini import generate_response


async def main():
    load_dotenv()
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("Не удалось загрузить GEMINI_API_KEY. Проверьте файл .env")

    prompt = "Привет! Как дела?"
    response = await generate_response(prompt, gemini_api_key)
    print(f"Промпт: {prompt}")
    print(f"Ответ: {response}")


if __name__ == "__main__":
    asyncio.run(main())
