import os
import asyncio
import re

from aiogram.types import Message

from bot.domain.DefaultSystemInstuction import anyaSystemInstruction
# Убираем импорт YANDEX_FOLDER_ID, так как он больше не нужен
# from bot.domain.const.env_const import YANDEX_FOLDER_ID 
from bot.data.repository.SessionRepository import SessionRepository
from bot.data.infrastructure.AnalyticsRepository import AnalyticsRepository
from bot.domain.repository.LLMRepository import LLMRepository

# --- Константы моделей ---
GEMINI_CHAT_MODEL = 'gemini-pro'
GEMINI_SUMMARIZE_MODEL = 'gemini-1.5-flash'
DEEPSEEK_CHAT_MODEL = 'deepseek-chat'
DEEPSEEK_SUMMARIZE_MODEL = 'deepseek-chat'
# Yandex модели больше не используются напрямую здесь
# YANDEX_CHAT_MODEL = ...
# YANDEX_SUMMARIZE_MODEL = ...


class ChatService:

    def __init__(
        self,
        session_repo: SessionRepository,
        analytics_repo: AnalyticsRepository,
        llm_client: LLMRepository,
    ):
        self.session_repo = session_repo
        self.analytics_repo = analytics_repo
        self.llm_client = llm_client
        self.system_prompt = None # Оставляем None, будет инициализирован при первом вызове

        # Логика выбора модели теперь полностью зависит от LLM_PROVIDER
        provider = os.getenv("LLM_PROVIDER", "deepseek").lower()
        if provider == 'deepseek':
            self.chat_model = DEEPSEEK_CHAT_MODEL
            self.summarize_model = DEEPSEEK_SUMMARIZE_MODEL
        elif provider == 'gemini':
            self.chat_model = GEMINI_CHAT_MODEL
            self.summarize_model = GEMINI_SUMMARIZE_MODEL
        # Логика для Yandex остается в llm_service, здесь она не нужна
        # elif provider == 'yandex':
        #     ...

    async def handle_user_message(
        self,
        message: Message,
        content: str,
    ) -> list[str]:

        messages_history = await self.session_repo.get_session_data(chat_id = message.chat.id)

        request_messages = []

        for msg in messages_history:
            role = "assistant" if msg['role'] == 'model' else msg['role']

            if request_messages and request_messages[-1]['role'] == role:
                request_messages[-1]['content'] += "\n" + msg['content']
            else:
                request_messages.append({"role": role, "content": msg['content']})

        request_messages.append({"role": "user", "content": content})

        # Инициализируем системный промпт, если он еще не задан
        if self.system_prompt is None:
            self.system_prompt = anyaSystemInstruction(user_nickname = message.chat.username)

        ai_response = await self.llm_client.generate_response(
            messages = request_messages,
            model = self.chat_model,
            system_prompt = self.system_prompt
        )

        asyncio.create_task(
            self.session_repo.add_text_message(
                message = message,
                role = "user",
                content = content,
            )
        )

        return truncate_ai_refusal(ai_response).split('\n')

    async def handle_self_message(
        self,
        message: Message,
    ):
        asyncio.create_task(
            self.session_repo.add_text_message(
                message = message,
                role = "assistant",
                content = message.text,
            )
        )

    async def _summarize_and_clear(self, user_id: int, old_summary: str, messages_to_summarize: list[dict]):
        print(f"INFO: Starting background summarization for user {user_id}")

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
            await self.session_repo.clear_chat_history(chat_id = user_id)
        except Exception as e:
            print(f"ERROR: Background summarization failed for user {user_id}: {e}")


def truncate_ai_refusal(text: str) -> str:
    if not text:
        return ""
    refusal_patterns = [
        r"я не могу обсужд[а-я ]+ эту тему",
        r"я н могу обсуждать",
        r"давайте поговорим о чём-нибудь ещё",
        r"извините, но я не могу",
        r"как искусственный интеллект, я"
    ]
    combined_pattern = re.compile("|".join(refusal_patterns), re.IGNORECASE)
    match = combined_pattern.search(text)
    if match:
        cleaned_text = text[:match.start()].strip()
        return cleaned_text
    return text.strip()
