import os
import asyncio
from bot.infrastructure.session_repo import SessionRepository
from bot.infrastructure.analytics_repo import AnalyticsRepository
from bot.services.gemini import generate_response

# Константы
CONTEXT_MESSAGES_LIMIT = 10
SUMMARIZATION_MODEL = 'models/gemma-3-4b-it' # Быстрая модель для суммаризации
CHAT_MODEL = 'models/gemma-3-12b-it' # Основная модель для чата

class ChatService:
    def __init__(self, session_repo: SessionRepository, analytics_repo: AnalyticsRepository):
        self.session_repo = session_repo
        self.analytics_repo = analytics_repo
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

    async def handle_user_message(self, user_id: int, username: str, text: str) -> str:
        # 1. Параллельная запись в аналитику (не ждем ее)
        asyncio.create_task(self.analytics_repo.log_event({
            "user_id": user_id,
            "username": username,
            "text": text,
            "event_type": "user_message"
        }))

        # 2. Получение контекста
        summary, messages = await self.session_repo.get_session_data(user_id)

        # 3. Формирование промпта
        prompt_parts = []
        if summary:
            prompt_parts.append(f"This is a summary of the previous conversation: {summary}")
        
        for msg in messages:
            prompt_parts.append(f"{msg['role']}: {msg['text']}")
        
        prompt_parts.append(f"user: {text}")
        full_prompt = "\n".join(prompt_parts)

        # 4. Запрос к Gemini
        ai_response = await generate_response(full_prompt, self.gemini_api_key, model=CHAT_MODEL)

        # 5. Сохранение сообщений (не ждем завершения перед отправкой ответа)
        # Это ускоряет ответ пользователю
        asyncio.create_task(self.session_repo.add_message(user_id, "user", text))
        asyncio.create_task(self.session_repo.add_message(user_id, "model", ai_response))

        # 6. Фоновая суммаризация
        if len(messages) + 2 > CONTEXT_MESSAGES_LIMIT:
            # Запускаем, но не ждем
            asyncio.create_task(self._summarize_and_clear(user_id, summary, messages + [{"role": "user", "text": text}, {"role": "model", "text": ai_response}]))

        return ai_response

    async def _summarize_and_clear(self, user_id: int, old_summary: str, messages_to_summarize: list[dict]):
        """
        Приватный метод для выполнения суммаризации в фоне.
        """
        print(f"INFO: Starting background summarization for user {user_id}")
        
        conversation = "\n".join([f"{msg['role']}: {msg['text']}" for msg in messages_to_summarize])
        
        prompt = f"Please summarize the following conversation, keeping all key facts and details. Previous summary was: '{old_summary}'. New conversation is:\n\n{conversation}"
        
        try:
            new_summary = await generate_response(prompt, self.gemini_api_key, model=SUMMARIZATION_MODEL)
            await self.session_repo.update_summary_and_clear_messages(user_id, new_summary)
        except Exception as e:
            print(f"ERROR: Background summarization failed for user {user_id}: {e}")
