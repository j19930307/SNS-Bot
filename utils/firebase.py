import os
from datetime import datetime

from dotenv import load_dotenv
from google.cloud import firestore
from google.oauth2 import service_account

from sns_type import SnsType
from utils.utils import base64_decode


class Firebase:
    def __init__(self):
        load_dotenv()
        creds_dict = base64_decode(os.environ["FIREBASE_ADMIN_KEY"])
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        self.__db = firestore.AsyncClient(
            project=creds_dict.get("project_id"),
            credentials=credentials,
        )

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _doc_ref(self, type: SnsType, id: str):
        return self.__db.collection(type.value).document(id)

    # -------------------------------------------------------------------------
    # Generic account operations
    # -------------------------------------------------------------------------

    async def add_account(
            self,
            type: SnsType,
            id: str,
            username: str,
            discord_channel_id: str,
            updated_at: datetime,
    ) -> None:
        await self._doc_ref(type, id).set(
            {
                "username": username,
                "discord_channel_id": discord_channel_id,
                "updated_at": updated_at,
            }
        )

    async def delete_account(self, type: SnsType, id: str) -> None:
        await self._doc_ref(type, id).delete()

    async def is_account_exists(self, type: SnsType, id: str) -> bool:
        doc = await self._doc_ref(type, id).get()
        return doc.exists

    async def get_documents(self, type: SnsType) -> list:
        return [doc async for doc in self.__db.collection(type.value).stream()]

    # -------------------------------------------------------------------------
    # updated_at helpers
    # -------------------------------------------------------------------------

    async def get_updated_at(self, type: SnsType, id: str) -> datetime:
        """Return the stored updated_at timestamp, or now() if the doc doesn't exist."""
        doc = await self._doc_ref(type, id).get()
        if doc.exists:
            return doc.to_dict()["updated_at"]
        return datetime.now()

    async def set_updated_at(self, type: SnsType, id: str, updated_at: datetime) -> None:
        await self._doc_ref(type, id).update({"updated_at": updated_at})

    # -------------------------------------------------------------------------
    # Subscription queries
    # -------------------------------------------------------------------------

    async def get_subscribed_list(self, type: SnsType) -> list:
        return [doc async for doc in self.__db.collection(type.value).stream()]

    async def get_subscribed_list_from_discord_id(
            self, type: SnsType, discord_id: str
    ) -> list[tuple[str, str]]:
        """Return (username, doc_id) pairs for the given Discord channel."""
        docs = await self.get_documents(type)
        return [
            (doc.get("username"), doc.id)
            for doc in docs
            if doc.get("discord_channel_id") == discord_id
        ]

    # -------------------------------------------------------------------------
    # YouTube-specific operations
    # -------------------------------------------------------------------------

    async def add_youtube_account(
            self,
            handle: str,
            channel_name: str,
            discord_channel_id: str,
            latest_video_id: str,
            latest_video_published_at: datetime,
            latest_short_id: str,
            latest_short_published_at: datetime,
            latest_stream_id: str,
            latest_stream_published_at: datetime,
    ) -> None:
        await self.__db.collection(SnsType.YOUTUBE.value).document(handle).set(
            {
                "channel_name": channel_name,
                "discord_channel_id": discord_channel_id,
                "latest_video": {
                    "id": latest_video_id,
                    "published_at": latest_video_published_at,
                },
                "latest_short": {
                    "id": latest_short_id,
                    "published_at": latest_short_published_at,
                },
                "latest_stream": {
                    "id": latest_stream_id,
                    "published_at": latest_stream_published_at,
                },
            }
        )

    async def get_youtube_subscribed_list_from_discord_id(
            self, discord_id: str
    ) -> list[str]:
        """Return YouTube handles subscribed by the given Discord channel."""
        docs = [doc async for doc in self.__db.collection(SnsType.YOUTUBE.value).stream()]
        return [doc.id for doc in docs if doc.get("discord_channel_id") == discord_id]

    # -------------------------------------------------------------------------
    # Berriz-specific operations
    # -------------------------------------------------------------------------

    async def add_berriz_account(
            self,
            username: str,
            community_id: str,
            board_id: str,
            discord_channel_id: str,
            updated_at: datetime,
    ) -> None:
        await self.__db.collection(SnsType.BERRIZ.value).document(username).set(
            {
                "community_id": community_id,
                "board_id": board_id,
                "discord_channel_id": discord_channel_id,
                "updated_at": updated_at,
            }
        )

    async def get_berriz_subscribed_list(self, discord_id: str) -> list[str]:
        """Return Berriz usernames subscribed by the given Discord channel."""
        docs = [doc async for doc in self.__db.collection(SnsType.BERRIZ.value).stream()]
        return [doc.id for doc in docs if doc.get("discord_channel_id") == discord_id]
