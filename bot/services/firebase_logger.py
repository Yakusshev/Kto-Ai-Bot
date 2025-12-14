import os
import asyncio
import firebase_admin
from firebase_admin import credentials, firestore

db = None

def init_firebase():
    """
    Инициализирует Firebase Admin SDK.
    """
    global db
    
    key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
    if not key_path:
        print("Warning: FIREBASE_SERVICE_ACCOUNT_KEY environment variable not set. Logging will be disabled.")
        return

    if not os.path.exists(key_path):
        print(f"Warning: Firebase service account key file not found at path: {key_path}. Logging is disabled.")
        return

    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        print("Firebase initialized successfully.")
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        db = None

async def log_message_to_history(user_id: int, data: dict):
    """
    Асинхронно записывает данные в под-коллекцию 'history' для конкретного пользователя.
    """
    if not db:
        print("DEBUG: Firestore client is not available. Skipping log.")
        return

    try:
        # Строим путь к под-коллекции
        user_doc_ref = db.collection("users").document(str(user_id))
        history_collection_ref = user_doc_ref.collection("history")
        
        # .add() создает новый документ с авто-ID
        # Используем to_thread для выполнения синхронной операции в отдельном потоке
        update_time, doc_ref = await asyncio.to_thread(history_collection_ref.add, data)
        
        print(f"SUCCESS: Logged message for user {user_id} with document ID: {doc_ref.id}")
    except Exception as e:
        print(f"CRITICAL: Failed to write to Firestore for user {user_id}: {e}")
