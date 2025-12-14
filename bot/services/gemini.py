import google.generativeai as genai


async def generate_response(prompt: str, api_key: str) -> str:
    """
    Генерирует ответ от Google Gemini.

    :param prompt: Текст для отправки в модель.
    :param api_key: Ваш API-ключ.
    :return: Сгенерированный текст или сообщение об ошибке.
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        print(f"Ошибка при обращении к Google Gemini: {e}")
        return "Ошибка обращения к AI"
