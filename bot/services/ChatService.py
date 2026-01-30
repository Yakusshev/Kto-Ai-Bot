import os
import asyncio
import re

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

# Формирование имени модели Яндекса
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
        else:  # Gemini по умолчанию
            self.chat_model = GEMINI_CHAT_MODEL
            self.summarize_model = GEMINI_SUMMARIZE_MODEL

    async def handle_user_message(
        self,
        message: Message,
        user_id: int,
        text: str,
    ) -> str:

        summary, messages_history = await self.session_repo.get_session_data(chat_id = user_id)

        request_messages = []
        if summary:
            request_messages.append({
                "role": "system",
                "content": f"This is a summary of the previous conversation: {summary}"
            })

        for msg in messages_history:
            # ИСПРАВЛЕНО: используем 'content' вместо 'text' (согласно схеме YDB)
            role = "assistant" if msg['role'] == 'model' else msg['role']
            request_messages.append({"role": role, "content": msg['content']})

        request_messages.append({"role": "user", "content": text})

        ai_response = await self.llm_client.generate_response(
            messages = request_messages,
            model = self.chat_model,
            system_prompt = self.system_prompt
        )

        asyncio.create_task(
            self.session_repo.add_message(
                message = message,
                role = "user",
            )
        )

        return self.humanize(ai_response)

    def humanize(
        self,
        text: str,
    ) -> str:
        text = re.sub(r'  +', '\n', text)
        return text

    async def handle_self_message(
        self,
        message: Message,
    ):
        asyncio.create_task(
            self.session_repo.add_message(
                message = message,
                role = "assistant"
            )
        )

    async def _summarize_and_clear(self, user_id: int, old_summary: str, messages_to_summarize: list[dict]):
        print(f"INFO: Starting background summarization for user {user_id}")

        # ИСПРАВЛЕНО: используем 'content' при сборке текста для суммаризации
        conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages_to_summarize])
        prompt = (
            f"Please summarize the following conversation, keeping all key facts and details. "
            f"Previous summary was: '{old_summary}'. "
            f"New conversation is:\n\n{conversation_text}"
        )

        summarization_messages = [{"role": "user", "content": prompt}]

        try:
            new_summary = await self.llm_client.generate_response(
                messages = summarization_messages,
                model = self.summarize_model,
                system_prompt = None
            )
            # Убедись, что этот метод реализован в SessionRepository
            await self.session_repo.clear_chat_history(chat_id = user_id)
            # Здесь можно добавить логику сохранения new_summary в отдельную таблицу или колонку
        except Exception as e:
            print(f"ERROR: Background summarization failed for user {user_id}: {e}")
