import google.generativeai as genai

async def generate_response(prompt: str, api_key: str, model: str) -> str:
    """
    Генерирует ответ от Google Gemini.

    :param prompt: Текст для отправки в модель.
    :param api_key: Ваш API-ключ.
    :param model: Название модели для использования.
    :return: Сгенерированный текст или сообщение об ошибке.
    """
    genai.configure(api_key=api_key)
    try:
        genai_model = genai.GenerativeModel(model)
        response = await genai_model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        print(f"Ошибка при обращении к Google Gemini (model: {model}): {e}")
        return "Ошибка обращения к AI"
