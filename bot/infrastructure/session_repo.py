import asyncio
from firebase_admin import firestore
from google.cloud.firestore_v1.client import Client

class SessionRepository:
    def __init__(self, db: Client):
        self.db = db

    async def get_session_data(self, user_id: int, session_id: str = "default") -> tuple[str, list[dict]]:
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

    async def add_message(self, user_id: int, role: str, text: str, session_id: str = "default"):
        """
        Добавляет новое сообщение в историю сессии.
        """
        message_data = {
            "role": role,
            "text": text,
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        messages_ref = self.db.collection("users").document(str(user_id)).collection("sessions").document(session_id).collection("messages")
        await asyncio.to_thread(messages_ref.add, message_data)

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
