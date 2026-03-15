"""ArXiv research paper fetcher — pulls papers via the ArXiv API."""

import hashlib
import logging
import re
import xml.etree.ElementTree as ET

import httpx

from app.models.document import Document

log = logging.getLogger(__name__)

ARXIV_API = "http://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}

# ArXiv subject categories
CATEGORIES: dict[str, str] = {
    "cs.AI": "Artificial Intelligence",
    "cs.LG": "Machine Learning",
    "cs.CL": "Computation and Language (NLP)",
    "cs.CV": "Computer Vision",
    "cs.SE": "Software Engineering",
    "cs.CR": "Cryptography and Security",
    "cs.DS": "Data Structures and Algorithms",
    "cs.DB": "Databases",
    "cs.DC": "Distributed Computing",
    "cs.NE": "Neural and Evolutionary Computing",
    "cs.RO": "Robotics",
    "stat.ML": "Machine Learning (Statistics)",
    "physics": "Physics",
    "math": "Mathematics",
    "q-bio": "Quantitative Biology",
    "econ": "Economics",
}

ARXIV_ID_PATTERN = re.compile(
    r"ArXiv ID:\s*([A-Za-z0-9./\-]+(?:v\d+)?)",
    re.IGNORECASE,
)


def _make_id(arxiv_id: str) -> str:
    """Generate a stable document ID from ArXiv paper ID."""
    return hashlib.sha256(arxiv_id.encode()).hexdigest()[:16]


def _clean_text(text: str) -> str:
    """Collapse whitespace and strip."""
    return re.sub(r"\s+", " ", text).strip()


def extract_arxiv_id_from_body(body: str) -> str | None:
    """Extract the ArXiv ID from stored document metadata text."""
    match = ARXIV_ID_PATTERN.search(body or "")
    return match.group(1) if match else None


def build_pdf_url(arxiv_id: str) -> str:
    """Build a direct PDF URL for an ArXiv paper."""
    return f"https://arxiv.org/pdf/{arxiv_id}.pdf"


async def fetch_papers(
    query: str = "machine learning",
    limit: int = 50,
    category: str = "",
    sort_by: str = "relevance",
) -> list[Document]:
    """Fetch research papers from ArXiv.

    Args:
        query: Search query (e.g. "transformer attention", "quantum computing").
        limit: Maximum number of papers to fetch (max 200 per API call).
        category: Optional ArXiv category filter (e.g. "cs.AI", "cs.LG").
        sort_by: Sort order — "relevance", "lastUpdatedDate", or "submittedDate".

    Returns:
        A list of Document models with paper content.
    """
    # Build the search query
    search_parts = []
    if query:
        search_parts.append(f"all:{query}")
    if category:
        search_parts.append(f"cat:{category}")

    search_query = " AND ".join(search_parts) if search_parts else "all:machine learning"

    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": min(limit, 200),
        "sortBy": sort_by,
        "sortOrder": "descending",
    }

    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={"User-Agent": "ryu-engine/1.0"},
    ) as client:
        resp = await client.get(ARXIV_API, params=params)
        resp.raise_for_status()

    return _parse_response(resp.text)


def _parse_response(xml_text: str) -> list[Document]:
    """Parse ArXiv Atom XML response into Document models."""
    documents: list[Document] = []
    root = ET.fromstring(xml_text)

    for entry in root.findall("atom:entry", ATOM_NS):
        # Extract ArXiv ID from the entry URL
        entry_id = entry.findtext("atom:id", default="", namespaces=ATOM_NS)
        arxiv_id = entry_id.split("/abs/")[-1] if "/abs/" in entry_id else entry_id

        title = entry.findtext("atom:title", default="", namespaces=ATOM_NS)
        title = _clean_text(title)

        summary = entry.findtext("atom:summary", default="", namespaces=ATOM_NS)
        summary = _clean_text(summary)

        if not title or not summary:
            continue

        # Authors
        authors = [
            a.findtext("atom:name", default="", namespaces=ATOM_NS)
            for a in entry.findall("atom:author", ATOM_NS)
        ]
        author_str = ", ".join(authors[:5])
        if len(authors) > 5:
            author_str += f" (+{len(authors) - 5} more)"

        # Categories
        cats = [c.get("term", "") for c in entry.findall("atom:category", ATOM_NS)]
        cat_str = ", ".join(cats[:5])

        # Published date
        published = entry.findtext("atom:published", default="", namespaces=ATOM_NS)
        date_str = published[:10] if published else ""

        # Build a rich body combining abstract + metadata
        body = f"Abstract: {summary}\n\nAuthors: {author_str}\nCategories: {cat_str}\nPublished: {date_str}\nArXiv ID: {arxiv_id}"

        documents.append(
            Document(
                id=_make_id(arxiv_id),
                title=title,
                body=body,
                author=author_str,
                created_at=0,
                source="arxiv",
                pdf_url=build_pdf_url(arxiv_id),
            )
        )

    return documents
