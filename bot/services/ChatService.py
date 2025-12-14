import logging
import os
import asyncio
from bot.infrastructure.SessionRepository import SessionRepository
from bot.infrastructure.AnalyticsRepository import AnalyticsRepository
from bot.services.gemini import generate_response

# Константы
CONTEXT_MESSAGES_LIMIT = 10
SUMMARIZATION_MODEL = 'models/gemma-3-4b-it'
CHAT_MODEL = 'models/gemma-3-4b-it'


class ChatService:
    def __init__(self, session_repo: SessionRepository, analytics_repo: AnalyticsRepository):
        self.session_repo = session_repo
        self.analytics_repo = analytics_repo
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

    async def handle_user_message(self, user_id: int, username: str, text: str) -> str:

        local_logger = logging.getLogger("handle_user_message")
        local_logger.setLevel(logging.DEBUG)

        local_logger.debug("Entering handle_user_message")
        asyncio.create_task(
            self.analytics_repo.log_event(
                {
                    "user_id": user_id,
                    "username": username,
                    "text": text,
                    "event_type": "user_message"
                }
            )
        )

        local_logger.debug("log_event started")
        summary, messages = await self.session_repo.get_session_data(user_id)

        local_logger.debug("get_session_data completed")
        prompt_parts = []
        if summary:
            prompt_parts.append(f"This is a summary of the previous conversation: {summary}")

        for msg in messages:
            prompt_parts.append(f"{msg['role']}: {msg['text']}")

        prompt_parts.append(f"user: {text}")
        full_prompt = "\n".join(prompt_parts)

        local_logger.debug("full prompt generated")
        ai_response = await generate_response(full_prompt, self.gemini_api_key, model=CHAT_MODEL)

        local_logger.debug("ai response received")
        asyncio.create_task(self.session_repo.add_message(user_id, "user", text))
        asyncio.create_task(self.session_repo.add_message(user_id, "model", ai_response))

        local_logger.debug("add message task started")
        if len(messages) + 2 > CONTEXT_MESSAGES_LIMIT:
            asyncio.create_task(
                self._summarize_and_clear(
                    user_id,
                    summary,
                    messages + [
                        {
                            "role": "user",
                            "text": text},
                        {
                            "role": "model",
                            "text": ai_response
                        }
                    ]
                )
            )

        local_logger.debug("ready to return answer")
        return ai_response

    async def _summarize_and_clear(self, user_id: int, old_summary: str, messages_to_summarize: list[dict]):
        print(f"INFO: Starting background summarization for user {user_id}")

        conversation = "\n".join([f"{msg['role']}: {msg['text']}" for msg in messages_to_summarize])

        prompt = f"Please summarize the following conversation, keeping all key facts and details. Previous summary was: '{old_summary}'. New conversation is:\n\n{conversation}"

        try:
            new_summary = await generate_response(prompt, self.gemini_api_key, model=SUMMARIZATION_MODEL)
            await self.session_repo.update_summary_and_clear_messages(user_id, new_summary)
        except Exception as e:
            print(f"ERROR: Background summarization failed for user {user_id}: {e}")
