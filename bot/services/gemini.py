import logging

import google.generativeai as genai

async def generate_response(prompt: str, api_key: str, model: str) -> str:
    """
    Генерирует ответ от Google Gemini.

    :param prompt: Текст для отправки в модель.
    :param api_key: Ваш API-ключ.
    :param model: Название модели для использования.
    :return: Сгенерированный текст или сообщение об ошибке.
    """

    logger = logging.getLogger("### generate_response")
    logger.setLevel(logging.DEBUG)
    genai.configure(api_key = api_key)

    # genai_model = genai.GenerativeModel(model_name=model)
    # response = await genai_model.generate_content_async(prompt)
    # return response.text

    try:
        genai_model = genai.GenerativeModel(model_name = model)
        response = await genai_model.generate_content_async(prompt)
        logger.debug(f'Успешный ответ от модели {model}): {response.text}')
        return response.text
    except Exception as e:
        logger.debug("Ошибка при обращении к Google Gemini (model: {}): {e}" + model + " " + e.__str__())
        return "Ошибка обращения к AI"
