import os
import asyncio

from aiogram.types import Message

from bot.domain.DefaultSystemInstuction import anyaSystemInstruction
from bot.domain.const.env_const import YANDEX_FOLDER_ID
from bot.data.infrastructure.SessionRepository import SessionRepository
from bot.data.infrastructure.AnalyticsRepository import AnalyticsRepository
from bot.services.llm_service import LLMClient

# --- Константы моделей ---
GEMINI_CHAT_MODEL = 'gemini-pro'
GEMINI_SUMMARIZE_MODEL = 'gemini-1.5-flash'
DEEPSEEK_CHAT_MODEL = 'deepseek-chat'
DEEPSEEK_SUMMARIZE_MODEL = 'deepseek-chat'

# Получаем Folder ID из .env для формирования имени модели Яндекса
YANDEX_CHAT_MODEL = f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite"
YANDEX_SUMMARIZE_MODEL = f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite"


class ChatService:

    def __init__(
            self,
            session_repo: SessionRepository,
            analytics_repo: AnalyticsRepository,
            llm_client: LLMClient,
    ):
        self.session_repo = session_repo
        self.analytics_repo = analytics_repo
        self.llm_client = llm_client
        self.system_prompt = anyaSystemInstruction()
        
        provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        if provider == 'yandex':
            if not YANDEX_FOLDER_ID:
                raise ValueError("YANDEX_FOLDER_ID должен быть указан в .env для YandexGPT")
            self.chat_model = YANDEX_CHAT_MODEL
            self.summarize_model = YANDEX_SUMMARIZE_MODEL
        elif provider == 'deepseek':
            self.chat_model = DEEPSEEK_CHAT_MODEL
            self.summarize_model = DEEPSEEK_SUMMARIZE_MODEL
        else: # Gemini по умолчанию
            self.chat_model = GEMINI_CHAT_MODEL
            self.summarize_model = GEMINI_SUMMARIZE_MODEL

    async def handle_user_message(
            self,
            message: Message,
            user_id: int,
            username: str,
            text: str,
    ) -> str:
        asyncio.create_task(self.analytics_repo.log_event({
            "user_id": user_id,
            "username": username,
            "text": text,
            "event_type": "user_message"
        }))

        summary, messages_history = await self.session_repo.get_session_data(user_id)

        request_messages = []
        if summary:
            request_messages.append({"role": "system", "content": f"This is a summary of the previous conversation: {summary}"})
        
        for msg in messages_history:
            # Заменяем 'model' на 'assistant' при чтении из БД
            role = "assistant" if msg['role'] == 'model' else msg['role']
            request_messages.append({"role": role, "content": msg['text']})
        
        request_messages.append({"role": "user", "content": text})

        ai_response = await self.llm_client.generate_response(
            messages=request_messages, 
            model=self.chat_model,
            system_prompt=self.system_prompt
        )

        # Сохраняем ответ с правильной ролью 'assistant'
        asyncio.create_task(
            coro = self.session_repo.add_message(
                message = message,
                role = "user",
            )
        )

        if len(messages_history) + 2 > 10:
            full_history_for_summary = messages_history + [
                {"role": "user", "text": text},
                # Также исправляем здесь
                {"role": "assistant", "text": ai_response}
            ]
            asyncio.create_task(self._summarize_and_clear(user_id, summary, full_history_for_summary))

        return ai_response

    async def handle_self_message(
            self,
            message: Message,
    ):
        asyncio.create_task(
            coro = self.session_repo.add_message(
                message = message,
                role = "assistant",
            )
        )

    async def _summarize_and_clear(self, user_id: int, old_summary: str, messages_to_summarize: list[dict]):
        print(f"INFO: Starting background summarization for user {user_id}")
        
        conversation_text = "\n".join([f"{msg['role']}: {msg['text']}" for msg in messages_to_summarize])
        prompt = f"Please summarize the following conversation, keeping all key facts and details. Previous summary was: '{old_summary}'. New conversation is:\n\n{conversation_text}"
        
        summarization_messages = [{"role": "user", "content": prompt}]

        try:
            new_summary = await self.llm_client.generate_response(
                messages=summarization_messages, 
                model=self.summarize_model,
                system_prompt=None
            )
            await self.session_repo.update_summary_and_clear_messages(user_id, new_summary)
        except Exception as e:
            print(f"ERROR: Background summarization failed for user {user_id}: {e}")
