import asyncio
from firebase_admin import firestore
from google.cloud.firestore_v1.client import Client

class AnalyticsRepository:
    def __init__(self, db: Client):
        self.db = db

    async def log_event(self, event_data: dict):
        """
        Записывает событие в коллекцию 'analytics_logs'.
        """
        try:
            event_data["timestamp"] = firestore.SERVER_TIMESTAMP
            await asyncio.to_thread(self.db.collection("analytics_logs").add, event_data)
        except Exception as e:
            print(f"CRITICAL: Failed to write to analytics_logs: {e}")
