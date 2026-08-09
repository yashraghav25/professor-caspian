"""
Caspian SDK integration — outbound notifications + channel setup.
Uses caspian_sdk.CommClient per SKILL.md.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from caspian_sdk import CommClient

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("caspian_client")


class CaspianClient:
    """Singleton wrapper around CommClient for SentinelAI."""

    _instance: Optional["CaspianClient"] = None

    def __init__(self):
        self._client: Optional[CommClient] = None
        self._email_connection_id: Optional[str] = None
        self._telegram_connection_id: Optional[str] = None
        self._email_address: Optional[str] = None
        self._telegram_address: Optional[str] = None
        self._behavior_prompt: str = ""
        self._initialized = False

    @classmethod
    def get(cls) -> "CaspianClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def is_ready(self) -> bool:
        return self._initialized and self._client is not None

    @property
    def email_address(self) -> Optional[str]:
        return self._email_address

    @property
    def behavior_prompt(self) -> str:
        return self._behavior_prompt

    def initialize(self) -> None:
        if self._initialized:
            return
        if not settings.caspian_api_key:
            logger.warning("CASPIAN_API_KEY not set — notifications disabled.")
            return

        self._client = CommClient()
        try:
            email = self._client.connect_email(username=settings.caspian_email_username)
            self._email_connection_id = email["id"]
            self._email_address = email.get("address")
            logger.info(f"Caspian email connected: {self._email_address}")
        except Exception as e:
            logger.error(f"Caspian email connect failed: {e}")

        if settings.telegram_bot_token:
            try:
                tg = self._client.connect_telegram(bot_token=settings.telegram_bot_token)
                self._telegram_connection_id = tg["id"]
                self._telegram_address = tg.get("address")
                logger.info(f"Caspian Telegram connected: {self._telegram_address}")
            except Exception as e:
                logger.error(f"Caspian Telegram connect failed: {e}")
        else:
            logger.info("TELEGRAM_BOT_TOKEN not set — instant Telegram alerts disabled.")

        try:
            self._behavior_prompt = self._client.behavior_prompt() or ""
        except Exception:
            self._behavior_prompt = ""

        self._initialized = True

    async def send_email(self, recipient: str, text: str) -> dict:
        if not self._client or not self._email_connection_id:
            raise RuntimeError("Caspian email channel not connected")
        return await asyncio.to_thread(
            self._client.initiate, self._email_connection_id, recipient, text
        )

    async def send_telegram(self, recipient: str, text: str) -> dict:
        if not self._client or not self._telegram_connection_id:
            raise RuntimeError("Caspian Telegram channel not connected")
        return await asyncio.to_thread(
            self._client.initiate, self._telegram_connection_id, recipient, text
        )

    async def poll_events(self, after_seq: int = 0, limit: int = 50) -> tuple[list[dict], int]:
        if not self._client:
            return [], after_seq
        events = await asyncio.to_thread(
            self._client.events, after_seq, limit
        )
        if not events:
            return [], after_seq
        max_seq = max(e.get("seq", after_seq) for e in events)
        return events, max_seq

    async def reply_in_conversation(self, conversation_id: str, text: str) -> dict:
        if not self._client:
            raise RuntimeError("Caspian client not initialized")
        return await asyncio.to_thread(self._client.send_message, conversation_id, text)


def get_caspian() -> CaspianClient:
    return CaspianClient.get()
