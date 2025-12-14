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
    print(f"DEBUG: Firebase key path from env: {key_path}")

    if not key_path:
        print("ERROR: FIREBASE_SERVICE_ACCOUNT_KEY environment variable not set. Logging is disabled.")
        return

    if not os.path.exists(key_path):
        print(f"ERROR: Firebase service account key file not found at path: {key_path}. Logging is disabled.")
        return

    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
            print("DEBUG: Firebase app initialized.")
        
        db = firestore.client()
        print("SUCCESS: Firebase initialized successfully and Firestore client is ready.")
    except Exception as e:
        print(f"CRITICAL: Error initializing Firebase: {e}")
        db = None

async def log_to_firestore(collection: str, data: dict):
    """
    Асинхронно записывает данные в указанную коллекцию Firestore.
    """
    if not db:
        print("DEBUG: Firestore client is not available. Skipping log.")
        return

    print(f"DEBUG: Attempting to log to Firestore collection '{collection}': {data}")
    try:
        doc_ref = db.collection(collection).document()
        # Используем to_thread для выполнения синхронной операции в отдельном потоке
        await asyncio.to_thread(doc_ref.set, data)
        print(f"SUCCESS: Logged to Firestore with document ID: {doc_ref.id}")
    except Exception as e:
        print(f"CRITICAL: Failed to write to Firestore: {e}")
