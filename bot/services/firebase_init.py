import os
from typing import Union
import firebase_admin
import json
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.client import Client

def init_firebase() -> Union[Client, None]:
    """
    Инициализирует Firebase Admin SDK и возвращает клиент Firestore.
    """
    key_path_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

    if not key_path_json:
        print("Warning: FIREBASE_SERVICE_ACCOUNT_JSON environment variable not set. Logging will be disabled.")
        return

    cred_dict = json.loads(key_path_json)

    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        print("Firebase initialized successfully.")
        return db
    except Exception as e:
        print(f"CRITICAL: Error initializing Firebase: {e}")
        return None
