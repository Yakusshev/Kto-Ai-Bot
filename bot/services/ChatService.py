import os
import asyncio
from bot.infrastructure.SessionRepository import SessionRepository
from bot.infrastructure.AnalyticsRepository import AnalyticsRepository
from bot.services.llm_service import LLMClient

# --- Константы моделей ---
GEMINI_CHAT_MODEL = 'gemini-pro'
GEMINI_SUMMARIZE_MODEL = 'gemini-1.5-flash'
DEEPSEEK_CHAT_MODEL = 'deepseek-chat'
DEEPSEEK_SUMMARIZE_MODEL = 'deepseek-chat'
YANDEX_CHAT_MODEL = 'yandexgpt-lite'
YANDEX_SUMMARIZE_MODEL = 'yandexgpt-lite'

class ChatService:
    def __init__(self, session_repo: SessionRepository, analytics_repo: AnalyticsRepository, llm_client: LLMClient):
        self.session_repo = session_repo
        self.analytics_repo = analytics_repo
        self.llm_client = llm_client
        self.system_prompt = os.getenv("SYSTEM_PROMPT")
        
        provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        if provider == 'yandex':
            self.chat_model = YANDEX_CHAT_MODEL
            self.summarize_model = YANDEX_SUMMARIZE_MODEL
        elif provider == 'deepseek':
            self.chat_model = DEEPSEEK_CHAT_MODEL
            self.summarize_model = DEEPSEEK_SUMMARIZE_MODEL
        else: # Gemini по умолчанию
            self.chat_model = GEMINI_CHAT_MODEL
            self.summarize_model = GEMINI_SUMMARIZE_MODEL

    async def handle_user_message(self, user_id: int, username: str, text: str) -> str:
        asyncio.create_task(self.analytics_repo.log_event({
            "user_id": user_id,
            "username": username,
            "text": text,
            "event_type": "user_message"
        }))

        summary, messages = await self.session_repo.get_session_data(user_id)

        prompt_parts = []
        if summary:
            prompt_parts.append(f"This is a summary of the previous conversation: {summary}")
        
        for msg in messages:
            prompt_parts.append(f"{msg['role']}: {msg['text']}")
        
        prompt_parts.append(f"user: {text}")
        full_prompt = "\\n".join(prompt_parts)

        ai_response = await self.llm_client.generate_response(
            prompt=full_prompt, 
            model=self.chat_model,
            system_prompt=self.system_prompt
        )

        asyncio.create_task(self.session_repo.add_message(user_id, "user", text))
        asyncio.create_task(self.session_repo.add_message(user_id, "model", ai_response))

        if len(messages) + 2 > 10:
            asyncio.create_task(self._summarize_and_clear(user_id, summary, messages + [{"role": "user", "text": text}, {"role": "model", "text": ai_response}]))

        return ai_response

    async def _summarize_and_clear(self, user_id: int, old_summary: str, messages_to_summarize: list[dict]):
        print(f"INFO: Starting background summarization for user {user_id}")
        
        conversation = "\\n".join([f"{msg['role']}: {msg['text']}" for msg in messages_to_summarize])
        
        prompt = f"Please summarize the following conversation, keeping all key facts and details. Previous summary was: '{old_summary}'. New conversation is:\\n\\n{conversation}"
        
        try:
            new_summary = await self.llm_client.generate_response(
                prompt=prompt, 
                model=self.summarize_model,
                system_prompt=None # Для суммаризации системный промпт не нужен
            )
            await self.session_repo.update_summary_and_clear_messages(user_id, new_summary)
        except Exception as e:
            print(f"ERROR: Background summarization failed for user {user_id}: {e}")
