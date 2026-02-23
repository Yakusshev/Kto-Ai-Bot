import base64
import os
from typing import Union
import firebase_admin
import json
import logging
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.client import Client
import asyncio

#TODO избавиться с помощью di
db = None

def init_firebase() -> Union[Client, None]:
    logger = logging.getLogger()
    """
    Инициализирует Firebase Admin SDK и возвращает клиент Firestore.
    """
    try:
        firebase_admin.get_app()
        return
    except ValueError:
        pass  # Приложение еще не создано, идем дальше

        # 1. Сценарий Amvera (Base64 переменная)
    b64_creds = os.getenv("FIREBASE_SERVICE_ACCOUNT_BASE64")

    global db

    if b64_creds:
        try:
            # Декодируем Base64 обратно в байты -> строку -> JSON
            json_str = base64.b64decode(b64_creds).decode("utf-8")
            cred_dict = json.loads(json_str)

            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            logger.info("Firebase initialized successfully via Base64 Env Var.")
            return db
        except Exception as e:
            logger.error(f"Failed to decode Firebase credentials from Base64: {e}")
            raise e


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

        print(f"SUCCESS: Logged message for user {user_id} with document ID: {doc_ref.chat_id}")
    except Exception as e:
        print(f"CRITICAL: Failed to write to Firestore for user {user_id}: {e}")
