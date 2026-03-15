"""Tests for ArXiv fetcher utilities."""

from app.services.arxiv_fetcher import (
    _make_id,
    _parse_response,
    build_pdf_url,
    extract_arxiv_id_from_body,
)


class TestMakeId:
    def test_deterministic(self):
        assert _make_id("2301.00001") == _make_id("2301.00001")

    def test_different_inputs_different_ids(self):
        assert _make_id("2301.00001") != _make_id("2301.00002")

    def test_length_is_16(self):
        assert len(_make_id("2301.00001v1")) == 16


class TestExtractArxivId:
    def test_extracts_from_body(self):
        body = "Abstract: blah\nArXiv ID: 2301.12345"
        assert extract_arxiv_id_from_body(body) == "2301.12345"

    def test_extracts_with_version(self):
        body = "ArXiv ID: 2301.12345v2"
        assert extract_arxiv_id_from_body(body) == "2301.12345v2"

    def test_returns_none_when_missing(self):
        assert extract_arxiv_id_from_body("no id here") is None

    def test_returns_none_for_empty(self):
        assert extract_arxiv_id_from_body("") is None

    def test_case_insensitive(self):
        body = "arxiv id: 2301.00001"
        assert extract_arxiv_id_from_body(body) == "2301.00001"


class TestBuildPdfUrl:
    def test_builds_correct_url(self):
        assert build_pdf_url("2301.12345") == "https://arxiv.org/pdf/2301.12345.pdf"

    def test_with_version(self):
        assert build_pdf_url("2301.12345v2") == "https://arxiv.org/pdf/2301.12345v2.pdf"


class TestParseResponse:
    SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>http://arxiv.org/abs/2301.00001v1</id>
        <title>  Test Paper Title  </title>
        <summary>  This is the abstract of the test paper.  </summary>
        <author><name>Alice Smith</name></author>
        <author><name>Bob Jones</name></author>
        <category term="cs.AI"/>
        <published>2023-01-01T00:00:00Z</published>
      </entry>
    </feed>"""

    def test_parses_single_entry(self):
        docs = _parse_response(self.SAMPLE_XML)
        assert len(docs) == 1

    def test_extracts_title(self):
        docs = _parse_response(self.SAMPLE_XML)
        assert docs[0].title == "Test Paper Title"

    def test_extracts_authors(self):
        docs = _parse_response(self.SAMPLE_XML)
        assert "Alice Smith" in docs[0].author
        assert "Bob Jones" in docs[0].author

    def test_body_contains_abstract(self):
        docs = _parse_response(self.SAMPLE_XML)
        assert "abstract of the test paper" in docs[0].body.lower()

    def test_body_contains_arxiv_id(self):
        docs = _parse_response(self.SAMPLE_XML)
        assert "2301.00001v1" in docs[0].body

    def test_source_is_arxiv(self):
        docs = _parse_response(self.SAMPLE_XML)
        assert docs[0].source == "arxiv"

    def test_pdf_url_set(self):
        docs = _parse_response(self.SAMPLE_XML)
        assert docs[0].pdf_url == "https://arxiv.org/pdf/2301.00001v1.pdf"

    def test_skips_entry_without_title(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <id>http://arxiv.org/abs/2301.00002v1</id>
            <title></title>
            <summary>Some abstract</summary>
          </entry>
        </feed>"""
        assert _parse_response(xml) == []
