"""Tests for PDF summarizer caching and rate limiting."""

import time
from unittest.mock import patch

import pytest

from app.services.paper_summarizer import (
    PdfSummaryError,
    PdfSummaryRateLimitError,
    _call_timestamps,
    _enforce_rate_limit,
    _extract_text_sections,
    _get_cached_summary,
    _set_cached_summary,
    _summary_cache,
)


@pytest.fixture(autouse=True)
def _clear_state():
    """Reset module-level caches/rate-limiter between tests."""
    _summary_cache.clear()
    _call_timestamps.clear()
    yield
    _summary_cache.clear()
    _call_timestamps.clear()


class TestCaching:
    def test_set_and_get(self):
        _set_cached_summary("doc1", "summary text")
        assert _get_cached_summary("doc1") == "summary text"

    def test_cache_miss(self):
        assert _get_cached_summary("nonexistent") is None

    def test_cache_expiry(self):
        _summary_cache["doc1"] = {
            "summary": "old summary",
            "expires_at": time.time() - 1,  # already expired
        }
        assert _get_cached_summary("doc1") is None
        # Expired entry should be removed
        assert "doc1" not in _summary_cache

    def test_cache_not_expired(self):
        _summary_cache["doc1"] = {
            "summary": "fresh summary",
            "expires_at": time.time() + 3600,
        }
        assert _get_cached_summary("doc1") == "fresh summary"


class TestRateLimiting:
    def test_allows_under_limit(self):
        # Should not raise when under limit
        _enforce_rate_limit()

    def test_blocks_at_limit(self):
        with patch("app.services.paper_summarizer.get_settings") as mock_settings:
            mock_settings.return_value.pdf_summary_max_calls_per_hour = 3
            _enforce_rate_limit()
            _enforce_rate_limit()
            _enforce_rate_limit()
            with pytest.raises(PdfSummaryRateLimitError):
                _enforce_rate_limit()

    def test_prunes_old_timestamps(self):
        # Add old timestamps outside the 1-hour window
        old_time = time.time() - 3700
        _call_timestamps.extend([old_time, old_time + 1])
        with patch("app.services.paper_summarizer.get_settings") as mock_settings:
            mock_settings.return_value.pdf_summary_max_calls_per_hour = 3
            # Old timestamps should get pruned, allowing new calls
            _enforce_rate_limit()
            assert len(_call_timestamps) == 1  # only the new one


class TestExtractTextSections:
    def _make_pdf_bytes(self, pages: list[str]) -> bytes:
        """Create a minimal PDF in-memory from text pages."""
        from io import BytesIO

        from pypdf import PdfWriter
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        writer = PdfWriter()
        for text in pages:
            buf = BytesIO()
            c = canvas.Canvas(buf, pagesize=letter)
            c.drawString(72, 700, text)
            c.showPage()
            c.save()
            buf.seek(0)
            from pypdf import PdfReader
            reader = PdfReader(buf)
            writer.add_page(reader.pages[0])

        out = BytesIO()
        writer.write(out)
        return out.getvalue()

    def test_extracts_text(self):
        try:
            from reportlab.pdfgen import canvas  # noqa: F401
        except ImportError:
            pytest.skip("reportlab not installed")

        pdf = self._make_pdf_bytes(["Hello World Page One"])
        text = _extract_text_sections(pdf, max_chars=5000)
        assert "Hello World" in text

    def test_empty_pdf_raises(self):
        from io import BytesIO

        from pypdf import PdfWriter

        writer = PdfWriter()
        buf = BytesIO()
        writer.write(buf)
        with pytest.raises(PdfSummaryError, match="no pages"):
            _extract_text_sections(buf.getvalue(), max_chars=5000)

    def test_respects_max_chars(self):
        try:
            from reportlab.pdfgen import canvas  # noqa: F401
        except ImportError:
            pytest.skip("reportlab not installed")

        pdf = self._make_pdf_bytes(["A" * 500] * 3)
        text = _extract_text_sections(pdf, max_chars=100)
        assert len(text) <= 100
