import asyncio

import ydb
from aiogram.types import Message
from ydb import SessionPool


class SessionRepository:

    def __init__(self, ydb_session_pool: SessionPool):
        self.ydb_session_pool = ydb_session_pool

    async def get_session_data(
            self,
            user_id: int,
            session_id: str = "default",
    ) -> tuple[str, list[dict]]:
        """
        Получает саммари и историю сообщений для сессии.
        """
        session_ref = self.db.collection("users").document(str(user_id)).collection("sessions").document(session_id)
        messages_ref = session_ref.collection("messages").order_by("timestamp", direction="ASCENDING")

        session_doc_task = asyncio.to_thread(session_ref.get)
        messages_docs_task = asyncio.to_thread(messages_ref.get)

        session_doc, messages_docs = await asyncio.gather(session_doc_task, messages_docs_task)

        summary = session_doc.to_dict().get("summary", "") if session_doc.exists else ""
        messages = [doc.to_dict() for doc in messages_docs]

        return summary, messages


    async def save_message(
            self,
            message: Message,
            role: str,
            content: str = None,
    ):
        # Если content не передан (для входящих), берем текст из сообщения
        final_content = content or message.text or message.caption or ""

        # Извлекаем данные о реплае и цитате
        reply_to_id = None
        text_quote = None
        if message.reply_to_message:
            reply_to_id = message.reply_to_message.message_id
            if message.quote:
                text_quote = message.quote.text

        query = """
            DECLARE $chat_id AS Uint64;
            DECLARE $created_at AS Timestamp;
            DECLARE $message_id AS Uint64;
            DECLARE $role AS Utf8;
            DECLARE $content AS Utf8;
            DECLARE $event_type AS Utf8;
            DECLARE $reply_to_id AS Uint64?;
            DECLARE $text_quote AS Utf8?;
            DECLARE $business_conn_id AS Utf8?;
    
            UPSERT INTO chat_events (
                chat_id, created_at, message_id, role, content, 
                event_type, reply_to_id, text_quote, business_conn_id
            ) VALUES (
                $chat_id, $created_at, $message_id, $role, $content, 
                $event_type, $reply_to_id, $text_quote, $business_conn_id
            );
        """

        def execute(session):
            session.transaction().execute(
                query,
                {
                    '$chat_id': message.chat.id,
                    '$created_at': message.datetime.now(),
                    '$message_id': message.message_id,
                    '$role': role,
                    '$content': final_content,
                    '$event_type': 'text',
                    '$reply_to_id': reply_to_id,
                    '$text_quote': text_quote,
                    '$business_conn_id': message.business_connection_id
                },
                commit_tx=True
            )

        return pool.retry_operation_sync(execute)

    async def update_summary_and_clear_messages(self, user_id: int, new_summary: str, session_id: str = "default"):
        """
        Атомарно обновляет саммари и удаляет все сообщения из под-коллекции.
        """
        session_ref = self.db.collection("users").document(str(user_id)).collection("sessions").document(session_id)
        messages_ref = session_ref.collection("messages")

        def batch_transaction():
            docs_to_delete = list(messages_ref.stream())
            batch = self.db.batch()
            batch.set(session_ref, {"summary": new_summary}, merge=True)
            for doc in docs_to_delete:
                batch.delete(doc.reference)
            batch.commit()

        await asyncio.to_thread(batch_transaction)
        print(f"SUCCESS: Summarized and cleared messages for user {user_id}")
