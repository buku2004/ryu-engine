"""Tests for text_processing utilities."""

from app.utils.text_processing import clean_text, prepare_embedding_text


class TestCleanText:
    def test_strips_markdown_links(self):
        assert clean_text("[click here](https://example.com)") == "click here"

    def test_removes_image_markdown(self):
        assert clean_text("![alt text](https://img.png)").strip() == ""

    def test_decodes_html_entities(self):
        assert clean_text("Tom &amp; Jerry") == "Tom & Jerry"

    def test_collapses_whitespace(self):
        assert clean_text("hello   world\n\nfoo") == "hello world foo"

    def test_empty_string(self):
        assert clean_text("") == ""

    def test_combined_cleaning(self):
        raw = "Read [this paper](http://arxiv.org)  &amp; ![logo](img.png) enjoy"
        result = clean_text(raw)
        assert "this paper" in result
        assert "http://arxiv.org" not in result
        assert "![" not in result
        assert "&amp;" not in result


class TestPrepareEmbeddingText:
    def test_combines_title_and_body(self):
        result = prepare_embedding_text("My Title", "Body content")
        assert result.startswith("My Title. Body content")

    def test_title_only_when_body_empty(self):
        result = prepare_embedding_text("Title Only", "")
        assert result == "Title Only"

    def test_truncates_to_8000_chars(self):
        long_body = "x" * 10000
        result = prepare_embedding_text("T", long_body)
        assert len(result) <= 8000

    def test_cleans_html_entities_in_input(self):
        result = prepare_embedding_text("A &amp; B", "C &lt; D")
        assert "&amp;" not in result
        assert "&lt;" not in result
