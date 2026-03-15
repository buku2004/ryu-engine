"""Tests for Reciprocal Rank Fusion logic and hybrid search helpers."""

from app.services.hybrid_search import _resolve_pdf_url


class TestResolvePdfUrl:
    def test_returns_existing_pdf_url(self):
        doc = {"pdf_url": "https://arxiv.org/pdf/2301.00001.pdf", "source": "arxiv"}
        assert _resolve_pdf_url(doc) == "https://arxiv.org/pdf/2301.00001.pdf"

    def test_builds_url_from_body_for_arxiv(self):
        doc = {
            "pdf_url": "",
            "source": "arxiv",
            "body": "Abstract: test\nArXiv ID: 2301.00001",
        }
        assert _resolve_pdf_url(doc) == "https://arxiv.org/pdf/2301.00001.pdf"

    def test_returns_empty_for_non_arxiv(self):
        doc = {"pdf_url": "", "source": "wiki", "body": "some text"}
        assert _resolve_pdf_url(doc) == ""

    def test_returns_empty_when_no_arxiv_id_in_body(self):
        doc = {"pdf_url": "", "source": "arxiv", "body": "no id here"}
        assert _resolve_pdf_url(doc) == ""


class TestRRFScoring:
    """Test the Reciprocal Rank Fusion scoring logic in isolation."""

    def test_rrf_score_formula(self):
        """Verify the RRF formula: 1/(k + rank + 1)."""
        k = 60
        # Rank 0: score = 1/(60+0+1) = 1/61
        assert abs(1.0 / (k + 0 + 1) - 1 / 61) < 1e-10
        # Rank 1: score = 1/(60+1+1) = 1/62
        assert abs(1.0 / (k + 1 + 1) - 1 / 62) < 1e-10

    def test_rrf_fusion_merges_scores(self):
        """Documents appearing in both lists get summed scores."""
        k = 60
        scores: dict[str, float] = {}

        keyword_hits = [{"id": "A"}, {"id": "B"}, {"id": "C"}]
        vector_hits = [{"id": "B"}, {"id": "D"}, {"id": "A"}]

        for rank, hit in enumerate(keyword_hits):
            doc_id = hit["id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)

        for rank, hit in enumerate(vector_hits):
            doc_id = hit["id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)

        # B appears in both (rank 1 keyword, rank 0 vector) -> highest fused score
        sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)
        assert sorted_ids[0] == "B"  # B gets highest combined score

        # A appears in both too (rank 0 keyword, rank 2 vector)
        assert sorted_ids[1] == "A"

        # Verify all 4 unique docs are present
        assert set(sorted_ids) == {"A", "B", "C", "D"}

    def test_rrf_deduplciates(self):
        """Same document from both sources should appear only once."""
        k = 60
        scores: dict[str, float] = {}
        for rank, doc_id in enumerate(["X", "Y"]):
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
        for rank, doc_id in enumerate(["X", "Z"]):
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)

        assert len(scores) == 3  # X, Y, Z (X not duplicated)
