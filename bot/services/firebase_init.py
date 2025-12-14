import os
from typing import Union
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.client import Client

def init_firebase() -> Union[Client, None]:
    """
    Инициализирует Firebase Admin SDK и возвращает клиент Firestore.
    """
    key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
    if not key_path:
        print("ERROR: FIREBASE_SERVICE_ACCOUNT_KEY not set.")
        return None

    if not os.path.exists(key_path):
        print(f"ERROR: Firebase service account key not found at: {key_path}")
        return None

    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        print("Firebase initialized successfully.")
        return db
    except Exception as e:
        print(f"CRITICAL: Error initializing Firebase: {e}")
        return None
