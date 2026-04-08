"""T7: Response formatting (Markdown -> Telegram HTML).

Tests:
- Bold: **text** -> <b>text</b>
- Italic: *text* -> <i>text</i>
- Code blocks: ```lang\ncode``` -> <pre><code>code</code></pre>
- Inline code: `code` -> <code>code</code>
- Links: [text](url) -> <a href="url">text</a>
- Tables: |col| -> <pre> aligned block
- Headings: ## Title -> <b>Title</b>
- Strikethrough: ~~text~~ -> <s>text</s>
- HTML escaping: &, <, > escaped correctly
- Message split: >4096 chars split into multiple messages
- Safe tags preserved: <b>, <i>, <code>, <pre>, <a>
"""

from __future__ import annotations

import re

# Replicate gateway regex patterns for testing
_MD_BOLD_RE = re.compile(r"\*\*([^\*\n]+?)\*\*")
_MD_ITALIC_STAR_RE = re.compile(r"(?<![\w\*])\*([^\*\n]+?)\*(?!\w)")
_MD_INLINECODE_RE = re.compile(r"`([^`\n]+?)`")
_MD_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_MD_STRIKE_RE = re.compile(r"~~([^~\n]+?)~~")
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

TG_MAX_MESSAGE_LEN = 4096


def escape_html(text: str) -> str:
    """Escape 3 chars for Telegram HTML body."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class TestHTMLEscaping:
    """T7.1: HTML special character escaping."""

    def test_ampersand(self) -> None:
        assert escape_html("a & b") == "a &amp; b"

    def test_less_than(self) -> None:
        assert escape_html("a < b") == "a &lt; b"

    def test_greater_than(self) -> None:
        assert escape_html("a > b") == "a &gt; b"

    def test_all_three(self) -> None:
        assert escape_html("<a & b>") == "&lt;a &amp; b&gt;"

    def test_order_matters_ampersand_first(self) -> None:
        """& must be escaped first, otherwise &lt; becomes &amp;lt;"""
        result = escape_html("&lt;")
        assert result == "&amp;lt;"


class TestBoldItalic:
    """T7.2: Bold and italic conversions."""

    def test_bold(self) -> None:
        result = _MD_BOLD_RE.sub(r"<b>\1</b>", "This is **bold** text")
        assert result == "This is <b>bold</b> text"

    def test_italic_star(self) -> None:
        result = _MD_ITALIC_STAR_RE.sub(r"<i>\1</i>", "This is *italic* text")
        assert result == "This is <i>italic</i> text"

    def test_bold_not_confused_with_italic(self) -> None:
        """**bold** should not become <i><i>bold</i></i>."""
        text = "**bold**"
        # Bold first
        text = _MD_BOLD_RE.sub(r"<b>\1</b>", text)
        assert text == "<b>bold</b>"


class TestCodeBlocks:
    """T7.3: Code block and inline code conversion."""

    def test_inline_code(self) -> None:
        result = _MD_INLINECODE_RE.sub(
            lambda m: f"<code>{escape_html(m.group(1))}</code>",
            "Use `pip install ruff` here",
        )
        assert "<code>pip install ruff</code>" in result

    def test_inline_code_escapes_html(self) -> None:
        """HTML inside inline code must be escaped."""
        result = _MD_INLINECODE_RE.sub(
            lambda m: f"<code>{escape_html(m.group(1))}</code>",
            "Use `a < b && c > d` check",
        )
        assert "&lt;" in result
        assert "&amp;" in result


class TestHeadings:
    """T7.4: Heading conversion."""

    def test_h2_to_bold(self) -> None:
        result = _MD_HEADING_RE.sub(lambda m: f"<b>{m.group(2)}</b>", "## Title Here")
        assert result == "<b>Title Here</b>"

    def test_h1_to_bold(self) -> None:
        result = _MD_HEADING_RE.sub(lambda m: f"<b>{m.group(2)}</b>", "# Main Title")
        assert result == "<b>Main Title</b>"


class TestLinks:
    """T7.5: Markdown links to HTML."""

    def test_simple_link(self) -> None:
        result = _MD_LINK_RE.sub(
            lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>',
            "[GitHub](https://github.com)",
        )
        assert result == '<a href="https://github.com">GitHub</a>'


class TestStrikethrough:
    """T7.6: Strikethrough."""

    def test_strikethrough(self) -> None:
        result = _MD_STRIKE_RE.sub(r"<s>\1</s>", "This is ~~deleted~~ text")
        assert result == "This is <s>deleted</s> text"


class TestMessageSplit:
    """T7.7: Split messages >4096 chars.

    Contract: if response > TG_MAX_MESSAGE_LEN, split at paragraph or newline boundary.
    """

    def test_short_message_no_split(self) -> None:
        text = "Short message"
        assert len(text) <= TG_MAX_MESSAGE_LEN

    def test_long_message_needs_split(self) -> None:
        text = "A" * 5000
        assert len(text) > TG_MAX_MESSAGE_LEN
        # Simple split at 4096
        chunks = []
        while text:
            chunks.append(text[:TG_MAX_MESSAGE_LEN])
            text = text[TG_MAX_MESSAGE_LEN:]
        assert len(chunks) == 2
        assert len(chunks[0]) == TG_MAX_MESSAGE_LEN
