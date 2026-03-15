"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from app.models.document import ArxivIngestRequest, Document
from app.models.search import SearchHit, SearchRequest


class TestDocument:
    def test_valid_document(self):
        doc = Document(id="abc", title="Test", body="Content")
        assert doc.id == "abc"
        assert doc.source == "unknown"
        assert doc.pdf_url == ""

    def test_defaults(self):
        doc = Document(id="1", title="T", body="B")
        assert doc.author == ""
        assert doc.created_at == 0


class TestArxivIngestRequest:
    def test_defaults(self):
        req = ArxivIngestRequest()
        assert req.query == "machine learning"
        assert req.limit == 50
        assert req.category == ""
        assert req.sort_by == "relevance"

    def test_limit_bounds(self):
        with pytest.raises(ValidationError):
            ArxivIngestRequest(limit=0)
        with pytest.raises(ValidationError):
            ArxivIngestRequest(limit=201)


class TestSearchRequest:
    def test_defaults(self):
        req = SearchRequest(q="test")
        assert req.mode == "hybrid"
        assert req.limit == 10
        assert req.offset == 0

    def test_invalid_mode(self):
        with pytest.raises(ValidationError):
            SearchRequest(q="test", mode="invalid")

    def test_valid_modes(self):
        for mode in ["hybrid", "keyword", "semantic"]:
            req = SearchRequest(q="test", mode=mode)
            assert req.mode == mode


class TestSearchHit:
    def test_defaults(self):
        hit = SearchHit(id="1", title="T", body="B")
        assert hit.score == 0.0
        assert hit.match_type == ""
        assert hit.pdf_url == ""
