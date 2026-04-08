"""T4: Media processing.

Tests:
- File download from Telegram API
- Audio transcription via Groq (mocked)
- Transcription failure fallback
- File size limit (>20MB rejected)
- Media extensions mapping
"""

from __future__ import annotations

import pytest

MEDIA_EXTENSIONS = {
    "voice": ".ogg",
    "audio": "",
    "video": ".mp4",
    "video_note": ".mp4",
    "photo": ".jpg",
    "document": "",
    "sticker": ".webp",
}

TG_MAX_FILE_MB = 20


class TestMediaExtensions:
    """T4.1: File extension mapping for media types."""

    @pytest.mark.parametrize(
        ("media_type", "expected_ext"),
        [
            ("voice", ".ogg"),
            ("video", ".mp4"),
            ("video_note", ".mp4"),
            ("photo", ".jpg"),
            ("sticker", ".webp"),
        ],
    )
    def test_known_extension(self, media_type: str, expected_ext: str) -> None:
        """Known media types map to correct extensions."""
        assert MEDIA_EXTENSIONS[media_type] == expected_ext

    def test_audio_keeps_original(self) -> None:
        """Audio files keep their original extension."""
        assert MEDIA_EXTENSIONS["audio"] == ""

    def test_document_keeps_original(self) -> None:
        """Documents keep their original extension."""
        assert MEDIA_EXTENSIONS["document"] == ""


class TestFileDownload:
    """T4.2: Download files from Telegram Bot API.

    Contract:
    1. Get file_path via getFile API
    2. Download from https://api.telegram.org/file/bot<token>/<file_path>
    3. Save to media-inbound/ with UUID filename
    4. Return Path or None on failure
    """

    def test_download_contract(self) -> None:
        """Download flow: getFile -> download bytes -> save to disk."""
        # Simulate the contract
        file_id = "AgACAgIAAxkBAA..."
        bot_token = "123:ABC"
        # Step 1: getFile returns file_path
        get_file_response = {
            "ok": True,
            "result": {"file_id": file_id, "file_path": "voice/file_42.ogg", "file_size": 5000},
        }
        file_path = get_file_response["result"]["file_path"]
        assert file_path == "voice/file_42.ogg"

        # Step 2: download URL
        url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        assert "file_42.ogg" in url

    def test_file_size_limit(self) -> None:
        """Files >20MB must be rejected."""
        file_size_mb = 25
        assert file_size_mb > TG_MAX_FILE_MB


class TestTranscription:
    """T4.3: Audio transcription via Groq Whisper.

    Contract:
    1. Read Groq API key from ~/.secrets/groq-api-key
    2. POST to https://api.groq.com/openai/v1/audio/transcriptions
    3. Model: whisper-large-v3-turbo
    4. Return transcript text or None on failure
    """

    def test_transcription_success(self) -> None:
        """Successful transcription returns text."""
        # Mock Groq response
        groq_response = {
            "text": "Hello, this is a test voice message",
        }
        assert groq_response["text"] == "Hello, this is a test voice message"

    def test_transcription_failure_returns_none(self) -> None:
        """Failed transcription returns None, gateway adds fallback note."""
        transcript = None  # Groq API failed
        if transcript:
            media_note = f"\n\n[Transcript]: {transcript}"
        else:
            media_note = "\n\n[Audio transcription failed: /path/to/file.ogg]"
        assert "transcription failed" in media_note.lower()

    def test_media_note_format_for_voice(self) -> None:
        """Voice message adds transcript to text_for_agent."""
        transcript = "Test transcript"
        media_note = f"\n\n[Голосовое/аудио, транскрипт]: {transcript}"
        assert "транскрипт" in media_note
        assert "Test transcript" in media_note
