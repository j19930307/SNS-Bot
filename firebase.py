import base64
import json
import os
from datetime import datetime

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore

from sns_type import SnsType


class Firebase:
    def __init__(self):
        load_dotenv()
        certificate = credentials.Certificate(self.base64_decode(os.environ["FIREBASE_ADMIN_KEY"]))
        firebase_admin.initialize_app(certificate)
        self.__db = firestore.client()

    # def get_updated_at(self, type: SnsType):
    #     doc_ref = self.__db.collection("artist").document(type.value)
    #     doc = doc_ref.get()
    #     if doc.exists:
    #         return doc.to_dict()['updated_at']
    #     else:
    #         return None
    #
    def set_updated_at(self, type: SnsType, id: str, updated_at: datetime):
        doc_ref = self.__db.collection(type.value).document(id)
        doc_ref.update({
            "updated_at": updated_at
        })

    def base64_decode(self, key) -> dict:
        decoded_bytes = base64.b64decode(key)
        decoded_string = decoded_bytes.decode('utf-8')
        return json.loads(decoded_string)

    def add_account(self, type: SnsType, id: str, username: str, discord_channel_id: str, updated_at: datetime):
        doc_ref = self.__db.collection(type.value).document(id)
        data = {
            "username": username,
            "discord_channel_id": discord_channel_id,
            "updated_at": updated_at
        }
        doc_ref.set(data)

    def get_documents(self, type: SnsType):
        return self.__db.collection(type.value).stream()

    def is_account_exists(self, type: SnsType, id: str):
        doc_ref = self.__db.collection(type.value).document(id)
        return doc_ref.get().exists

    def delete_account(self, type: SnsType, id: str):
        return self.__db.collection(type.value).document(id).delete()

    def get_subscribed_list(self, type: SnsType):
        return self.__db.collection(type.value).stream()

    def get_subscribed_list_from_discord_id(self, type: SnsType, discord_id: str):
        docs = self.__db.collection(type.value).stream()
        return [(doc.get("username"), doc.id) for doc in docs if doc.get("discord_channel_id") == discord_id]
