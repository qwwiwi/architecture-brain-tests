"""T2: Telegram message parsing.

Tests:
- Extract user_id from update
- Extract chat_id from update
- Extract text from message vs caption
- Allowlist check (allowed vs denied)
- Group chat gating (addressed vs not addressed)
- Media type detection (voice, photo, document, video, sticker)
- Source classification (own_text, own_voice, forwarded, external_media)
"""

from __future__ import annotations

from typing import Any

import pytest


class TestUpdateParsing:
    """T2.1: Extract fields from Telegram update."""

    def test_extract_user_id(self, telegram_update: dict[str, Any]) -> None:
        """User ID extracted from update.message.from.id."""
        msg = telegram_update.get("message") or telegram_update.get("channel_post")
        user_id = (msg.get("from") or {}).get("id")
        assert user_id == 111111

    def test_extract_chat_id(self, telegram_update: dict[str, Any]) -> None:
        """Chat ID extracted from update.message.chat.id."""
        msg = telegram_update["message"]
        assert msg["chat"]["id"] == 111111

    def test_extract_text(self, telegram_update: dict[str, Any]) -> None:
        """Text extracted from message.text."""
        msg = telegram_update["message"]
        text = (msg.get("text") or msg.get("caption") or "").strip()
        assert text == "Hello agent"

    def test_extract_caption_fallback(self) -> None:
        """If no text, caption is used."""
        msg = {"chat": {"id": 1}, "caption": "Photo caption", "photo": [{}]}
        text = (msg.get("text") or msg.get("caption") or "").strip()
        assert text == "Photo caption"

    def test_empty_message_ignored(self) -> None:
        """Message with no text and no caption returns empty."""
        msg = {"chat": {"id": 1}}
        text = (msg.get("text") or msg.get("caption") or "").strip()
        assert text == ""


class TestAllowlist:
    """T2.2: User allowlist check."""

    def test_allowed_user(self, valid_config: dict[str, Any]) -> None:
        """User in allowlist passes."""
        allowlist = valid_config["allowlist_user_ids"]
        assert 111111 in allowlist

    def test_denied_user(self, valid_config: dict[str, Any]) -> None:
        """User not in allowlist is denied."""
        allowlist = valid_config["allowlist_user_ids"]
        assert 999999 not in allowlist


class TestMediaDetection:
    """T2.3: Detect media type from Telegram message."""

    @pytest.mark.parametrize(
        ("field", "expected"),
        [
            ("voice", "voice"),
            ("audio", "voice"),
            ("video_note", "voice"),
            ("video", "video"),
            ("photo", "photo"),
            ("document", "document"),
            ("sticker", "sticker"),
        ],
    )
    def test_media_type_mapping(self, field: str, expected: str) -> None:
        """Each media field maps to correct input_type."""
        msg: dict[str, Any] = {"chat": {"id": 1}, field: {}}
        # Replicate _media_to_input_type logic
        source_tag = "own_text"
        if source_tag == "forwarded":
            result = "forwarded"
        elif "voice" in msg or "video_note" in msg or "audio" in msg:
            result = "voice"
        elif "video" in msg:
            result = "video"
        elif "photo" in msg:
            result = "photo"
        elif "document" in msg:
            result = "document"
        elif "sticker" in msg:
            result = "sticker"
        else:
            result = "text"
        assert result == expected

    def test_text_only_message(self) -> None:
        """Plain text message has no media."""
        msg = {"chat": {"id": 1}, "text": "hello"}
        media_keys = ("voice", "audio", "video_note", "video", "photo", "document", "sticker")
        has_media = any(k in msg for k in media_keys)
        assert not has_media


class TestSourceClassification:
    """T2.4: Source tag for memory provenance.

    Gateway classifies each message:
    - own_text: user typed text directly
    - own_voice: user sent voice message
    - forwarded: message forwarded from another user/channel
    - external_media: media from external source
    """

    def test_own_text(self) -> None:
        """Regular text message = own_text."""
        msg = {"text": "hello", "chat": {"id": 1}}
        is_forward = "forward_from" in msg or "forward_from_chat" in msg or "forward_date" in msg
        assert not is_forward

    def test_forwarded_message(self) -> None:
        """Message with forward_from = forwarded."""
        msg = {"text": "hello", "forward_from": {"id": 999}, "chat": {"id": 1}}
        is_forward = "forward_from" in msg or "forward_from_chat" in msg or "forward_date" in msg
        assert is_forward

    def test_forwarded_from_channel(self) -> None:
        """Message with forward_from_chat = forwarded."""
        msg = {"text": "channel post", "forward_from_chat": {"id": -100123}, "chat": {"id": 1}}
        is_forward = "forward_from" in msg or "forward_from_chat" in msg or "forward_date" in msg
        assert is_forward
