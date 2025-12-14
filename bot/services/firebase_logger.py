import os
import asyncio
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.firestore import SERVER_TIMESTAMP

db = None

def init_firebase():
    """
    Инициализирует Firebase Admin SDK.
    Путь к файлу ключа берется из переменной окружения FIREBASE_SERVICE_ACCOUNT_KEY.
    """
    global db
    
    key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
    if not key_path or not os.path.exists(key_path):
        print("Warning: Firebase service account key not found. Logging will be disabled.")
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

async def log_to_firestore(collection: str, data: dict):
    """
    Асинхронно записывает данные в указанную коллекцию Firestore.
    """
    if not db:
        return

    doc_ref = db.collection(collection).document()
    
    # Используем to_thread для выполнения синхронной операции в отдельном потоке
    await asyncio.to_thread(doc_ref.set, data)
