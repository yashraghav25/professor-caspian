"""
Caspian SDK integration — outbound notifications + channel setup.
Uses caspian_sdk.CommClient per SKILL.md.
"""

from __future__ import annotations

import asyncio
from typing import Optional

import httpx
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
        self._telegram_conversation_id: Optional[str] = None
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
    def telegram_address(self) -> Optional[str]:
        return self._telegram_address

    @property
    def telegram_ready(self) -> bool:
        return bool(self._telegram_connection_id and self._telegram_conversation_id)

    @property
    def behavior_prompt(self) -> str:
        return self._behavior_prompt

    def set_telegram_conversation(self, conversation_id: str) -> None:
        self._telegram_conversation_id = conversation_id
        logger.info(f"Telegram conversation cached: {conversation_id}")

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
                self._refresh_telegram_conversation()
            except Exception as e:
                logger.error(f"Caspian Telegram connect failed: {e}")
        else:
            logger.info("TELEGRAM_BOT_TOKEN not set — instant Telegram alerts disabled.")

        try:
            self._behavior_prompt = self._client.behavior_prompt() or ""
        except Exception:
            self._behavior_prompt = ""

        self._initialized = True

    def _refresh_telegram_conversation(self) -> None:
        """Telegram has no cold-initiate — reuse an existing conversation."""
        if not self._client or not self._telegram_connection_id:
            return
        try:
            convs = self._client.list_conversations(connection_id=self._telegram_connection_id)
            if convs:
                self._telegram_conversation_id = convs[0]["id"]
                logger.info(f"Telegram conversation ready: {self._telegram_conversation_id}")
            else:
                logger.warning(
                    "No Telegram conversation yet — message @%s once to enable instant alerts.",
                    (self._telegram_address or "your_bot").lstrip("@"),
                )
        except Exception as e:
            logger.error(f"Failed to list Telegram conversations: {e}")

    async def send_email(
        self,
        recipient: str,
        subject: str,
        text: str,
        html: str | None = None,
    ) -> dict:
        """Send email via Caspian initiate with subject + HTML body."""
        if not self._client or not self._email_connection_id:
            raise RuntimeError("Caspian email channel not connected")

        payload = {"recipient": recipient, "subject": subject, "text": text}
        if html:
            payload["html"] = html

        return await asyncio.to_thread(self._initiate_raw, self._email_connection_id, payload)

    def _initiate_raw(self, connection_id: str, payload: dict) -> dict:
        """Full initiate payload (subject, html) — SDK wrapper only passes text."""
        url = f"{settings.caspian_base_url.rstrip('/')}/v1/connections/{connection_id}/initiate"
        headers = {
            "Authorization": f"Bearer {settings.caspian_api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=30) as http:
            resp = http.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def send_telegram(self, text: str, blocks: list[dict] | None = None) -> dict:
        """
        Send Telegram alert via send_message on existing conversation.
        Telegram bots cannot cold-initiate — user must message the bot first.
        """
        if not self._client or not self._telegram_connection_id:
            raise RuntimeError("Caspian Telegram channel not connected")

        if not self._telegram_conversation_id:
            self._refresh_telegram_conversation()

        if not self._telegram_conversation_id:
            raise RuntimeError(
                f"Message {(self._telegram_address or 'the bot')} on Telegram first "
                "to open a conversation, then retry."
            )

        return await asyncio.to_thread(
            self._client.send_message, self._telegram_conversation_id, text, None, blocks
        )

    async def poll_events(self, after_seq: int = 0, limit: int = 50) -> tuple[list[dict], int]:
        if not self._client:
            return [], after_seq
        events = await asyncio.to_thread(self._client.events, after_seq, limit)
        if not events:
            return [], after_seq
        max_seq = max(e.get("seq", after_seq) for e in events)
        return events, max_seq

    async def reply_in_conversation(self, conversation_id: str, text: str) -> dict:
        if not self._client:
            raise RuntimeError("Caspian client not initialized")
        return await asyncio.to_thread(self._client.send_message, conversation_id, text)

    async def reply_to_message(
        self, message_id: str, text: str, blocks: list[dict] | None = None
    ) -> dict:
        """Reply to the exact inbound Caspian message on its original channel."""
        if not self._client:
            raise RuntimeError("Caspian client not initialized")
        return await asyncio.to_thread(self._client.reply, message_id, text, None, blocks)


def get_caspian() -> CaspianClient:
    return CaspianClient.get()
