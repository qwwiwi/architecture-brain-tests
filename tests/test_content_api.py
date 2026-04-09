"""T15: Content API endpoint validation.

Tests for bugs discovered during live episode publication (2026-04-09):
- UUID content_id handling (was: int only -> 404 on UUID)
- video_id extraction from material_url (was: None despite URL existing)
- Tariff/tier access control (was: admin had wrong tariff -> 403)
- Supabase fallback response mapping
"""

from __future__ import annotations

import re

import pytest


# --- Pure logic extracted from platform_api.py for unit testing ---

def is_uuid(content_id: str) -> bool:
    """Detect UUID content ID (Supabase) vs integer (SQLite legacy)."""
    return "-" in content_id and len(content_id) == 36


def extract_video_id(material_url: str | None) -> str | None:
    """Extract Kinescope video ID from material_url.

    Input: https://kinescope.io/embed/303fbe4f-4978-4e63-b416-0e0256088023
    Output: 303fbe4f-4978-4e63-b416-0e0256088023
    """
    mat_url = material_url or ""
    if not mat_url:
        return None
    video_id = mat_url.split("/")[-1] if "/" in mat_url else mat_url
    return video_id or None


TARIFF_ORDER = {"edge": 1, "pro": 2, "vip": 3}


def tariff_rank(tariff: str | None) -> int:
    """Get numeric rank for tariff. None/unknown = 0."""
    return TARIFF_ORDER.get(tariff or "", 0)


def check_access(user_tariff: str | None, content_tier: str | None) -> bool:
    """Check if user tariff grants access to content tier."""
    return tariff_rank(user_tariff) >= tariff_rank(content_tier)


def map_supabase_response(sr: dict) -> dict:
    """Map Supabase knowledge_items row to API response format."""
    mat_url = sr.get("material_url") or ""
    video_id = mat_url.split("/")[-1] if "/" in mat_url else mat_url
    return {
        "id": sr["id"],
        "slug": sr.get("slug"),
        "title": sr.get("title"),
        "description": sr.get("description"),
        "cover_url": None,
        "category": sr.get("category"),
        "content_type": sr.get("category"),
        "video_id": video_id or None,
        "text_content": sr.get("full_description", ""),
        "duration_minutes": sr.get("estimated_time"),
        "tariff_required": sr.get("tier", "edge"),
    }


# --- Test fixtures ---

SAMPLE_UUID = "29e70aed-50bc-4355-b663-2873b02ebd2a"
SAMPLE_KINESCOPE_URL = (
    "https://kinescope.io/embed/303fbe4f-4978-4e63-b416-0e0256088023"
)
SAMPLE_VIDEO_ID = "303fbe4f-4978-4e63-b416-0e0256088023"

SAMPLE_SUPABASE_ROW = {
    "id": SAMPLE_UUID,
    "slug": "live-claude-code-migration-2026-04-09",
    "title": "Claude Code: migration, architecture, memory, Telegram",
    "description": "Live episode about Claude Code setup",
    "full_description": "<h2>Content</h2><p>Detailed HTML...</p>",
    "category": "live",
    "tier": "pro",
    "difficulty": "intermediate",
    "estimated_time": 157,
    "tags": ["claude-code", "architecture"],
    "is_published": True,
    "sort_order": 1,
    "material_url": SAMPLE_KINESCOPE_URL,
    "transcript": "Full transcript text...",
    "created_at": "2026-04-09T10:00:00Z",
    "updated_at": "2026-04-09T10:00:00Z",
}


class TestUUIDDetection:
    """T15.1: UUID vs integer content_id detection."""

    def test_standard_uuid_detected(self) -> None:
        """Standard UUID-4 is detected."""
        assert is_uuid(SAMPLE_UUID) is True

    def test_integer_id_not_uuid(self) -> None:
        """Integer string is not UUID."""
        assert is_uuid("42") is False

    def test_short_string_not_uuid(self) -> None:
        """Short string with dashes is not UUID."""
        assert is_uuid("abc-def") is False

    def test_slug_not_uuid(self) -> None:
        """Content slug is not UUID."""
        assert is_uuid("live-claude-code-migration-2026-04-09") is False

    def test_uuid_without_dashes_not_detected(self) -> None:
        """UUID without dashes (32 hex chars) is not detected."""
        assert is_uuid("29e70aed50bc4355b6632873b02ebd2a") is False

    def test_36_char_string_with_dashes_is_uuid(self) -> None:
        """Any 36-char string with dashes passes (relaxed check)."""
        assert is_uuid("xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx") is True

    def test_empty_string_not_uuid(self) -> None:
        """Empty string is not UUID."""
        assert is_uuid("") is False


class TestVideoIdExtraction:
    """T15.2: video_id extraction from material_url.

    BUG: video_id was returning None despite material_url existing.
    Root cause: material_url not in supa_select columns or empty string.
    """

    def test_kinescope_embed_url(self) -> None:
        """Extract ID from Kinescope embed URL."""
        result = extract_video_id(SAMPLE_KINESCOPE_URL)
        assert result == SAMPLE_VIDEO_ID

    def test_kinescope_watch_url(self) -> None:
        """Extract ID from Kinescope watch URL."""
        url = "https://kinescope.io/watch/303fbe4f-4978-4e63-b416-0e0256088023"
        result = extract_video_id(url)
        assert result == "303fbe4f-4978-4e63-b416-0e0256088023"

    def test_bare_video_id(self) -> None:
        """Bare video ID (no URL) returns as-is."""
        result = extract_video_id("303fbe4f-4978-4e63-b416-0e0256088023")
        assert result == "303fbe4f-4978-4e63-b416-0e0256088023"

    def test_none_returns_none(self) -> None:
        """None material_url returns None."""
        assert extract_video_id(None) is None

    def test_empty_string_returns_none(self) -> None:
        """Empty string returns None."""
        assert extract_video_id("") is None

    def test_url_with_trailing_slash(self) -> None:
        """URL with trailing slash returns empty -> None."""
        result = extract_video_id("https://kinescope.io/embed/")
        assert result is None


class TestTariffAccess:
    """T15.3: Tariff/tier access control.

    BUG: Admin had tariff 'edge' (rank 1) but live episode
    required 'pro' (rank 2), causing 403 Upgrade Required.
    """

    def test_vip_accesses_everything(self) -> None:
        """VIP user can access all tiers."""
        assert check_access("vip", "edge") is True
        assert check_access("vip", "pro") is True
        assert check_access("vip", "vip") is True

    def test_pro_accesses_pro_and_edge(self) -> None:
        """Pro user can access pro and edge."""
        assert check_access("pro", "edge") is True
        assert check_access("pro", "pro") is True
        assert check_access("pro", "vip") is False

    def test_edge_only_accesses_edge(self) -> None:
        """Edge user can only access edge tier."""
        assert check_access("edge", "edge") is True
        assert check_access("edge", "pro") is False
        assert check_access("edge", "vip") is False

    def test_none_tariff_accesses_nothing(self) -> None:
        """User with no tariff has rank 0."""
        assert check_access(None, "edge") is False
        assert check_access(None, "pro") is False

    def test_none_tier_always_accessible(self) -> None:
        """Content with no tier is accessible to everyone."""
        assert check_access("edge", None) is True
        assert check_access(None, None) is True

    def test_edge_cannot_access_pro_content(self) -> None:
        """Exact reproduction of the 403 bug."""
        assert check_access("edge", "pro") is False

    def test_tariff_rank_ordering(self) -> None:
        """Tariff ranks: edge(1) < pro(2) < vip(3)."""
        assert tariff_rank("edge") < tariff_rank("pro")
        assert tariff_rank("pro") < tariff_rank("vip")

    def test_unknown_tariff_rank_zero(self) -> None:
        """Unknown tariff string returns 0."""
        assert tariff_rank("free") == 0
        assert tariff_rank("premium") == 0


class TestSupabaseResponseMapping:
    """T15.4: Supabase row -> API response mapping.

    BUG: video_id was None because material_url was not in
    supa_select columns list, or extraction logic was broken.
    """

    def test_video_id_extracted(self) -> None:
        """video_id is correctly extracted from material_url."""
        result = map_supabase_response(SAMPLE_SUPABASE_ROW)
        assert result["video_id"] == SAMPLE_VIDEO_ID

    def test_category_maps_to_content_type(self) -> None:
        """category field maps to both category and content_type."""
        result = map_supabase_response(SAMPLE_SUPABASE_ROW)
        assert result["category"] == "live"
        assert result["content_type"] == "live"

    def test_tier_maps_to_tariff_required(self) -> None:
        """tier field maps to tariff_required."""
        result = map_supabase_response(SAMPLE_SUPABASE_ROW)
        assert result["tariff_required"] == "pro"

    def test_full_description_maps_to_text_content(self) -> None:
        """full_description maps to text_content."""
        result = map_supabase_response(SAMPLE_SUPABASE_ROW)
        assert "Content" in result["text_content"]

    def test_cover_url_always_none(self) -> None:
        """cover_url is None for Supabase items (no field)."""
        result = map_supabase_response(SAMPLE_SUPABASE_ROW)
        assert result["cover_url"] is None

    def test_missing_material_url_gives_none_video_id(self) -> None:
        """Row without material_url gives video_id=None."""
        row = {**SAMPLE_SUPABASE_ROW, "material_url": None}
        result = map_supabase_response(row)
        assert result["video_id"] is None

    def test_empty_material_url_gives_none_video_id(self) -> None:
        """Row with empty material_url gives video_id=None."""
        row = {**SAMPLE_SUPABASE_ROW, "material_url": ""}
        result = map_supabase_response(row)
        assert result["video_id"] is None

    def test_default_tier_is_edge(self) -> None:
        """Missing tier defaults to 'edge'."""
        row = {k: v for k, v in SAMPLE_SUPABASE_ROW.items() if k != "tier"}
        result = map_supabase_response(row)
        assert result["tariff_required"] == "edge"

    def test_id_preserved(self) -> None:
        """UUID id is preserved in response."""
        result = map_supabase_response(SAMPLE_SUPABASE_ROW)
        assert result["id"] == SAMPLE_UUID

    def test_slug_preserved(self) -> None:
        """Slug is preserved in response."""
        result = map_supabase_response(SAMPLE_SUPABASE_ROW)
        assert result["slug"] == "live-claude-code-migration-2026-04-09"


class TestContentIdValidation:
    """T15.5: Content ID parsing edge cases."""

    def test_integer_string_valid(self) -> None:
        """'42' is a valid integer content_id."""
        assert not is_uuid("42")
        assert int("42") == 42

    def test_uuid_string_valid(self) -> None:
        """Standard UUID is valid content_id."""
        assert is_uuid(SAMPLE_UUID)

    def test_negative_integer_not_uuid(self) -> None:
        """Negative integer is not UUID."""
        assert not is_uuid("-1")

    def test_float_string_not_uuid(self) -> None:
        """Float string is not UUID."""
        assert not is_uuid("3.14")

    def test_uuid_regex_format(self) -> None:
        """UUID matches standard format."""
        pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        assert re.match(pattern, SAMPLE_UUID)
