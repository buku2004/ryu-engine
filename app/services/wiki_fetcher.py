"""Fandom/MediaWiki data fetcher — pulls articles from any Fandom wiki."""

import hashlib
import logging
import re

import httpx
from app.config import get_settings
from app.models.document import Document

log = logging.getLogger(__name__)

# Default wiki for Minecraft
DEFAULT_WIKI = "minecraft"


def _strip_html(html_text: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    text = re.sub(r"<[^>]+>", " ", html_text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _make_id(wiki: str, title: str) -> str:
    """Generate a stable document ID from wiki name + article title."""
    raw = f"{wiki}:{title}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


async def fetch_articles(
    wiki: str = DEFAULT_WIKI,
    limit: int = 50,
    category: str = "",
) -> list[Document]:
    """Fetch articles from a Fandom wiki via the MediaWiki API.

    Args:
        wiki: Fandom wiki subdomain (e.g. "minecraft", "zelda").
        limit: Maximum number of articles to fetch.
        category: Optional category name to filter articles (e.g. "Blocks", "Mobs").

    Returns:
        A list of Document models with article content.
    """
    base_url = f"https://{wiki}.fandom.com/api.php"
    documents: list[Document] = []

    if category:
        titles = await _fetch_category_titles(base_url, category, limit)
    else:
        titles = await _fetch_all_titles(base_url, limit)

    # Fetch full content in batches of 20 (MediaWiki API limit per request)
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(0, len(titles), 20):
            batch = titles[i : i + 20]
            docs = await _fetch_page_contents(client, base_url, wiki, batch)
            documents.extend(docs)

    return documents


async def _fetch_all_titles(base_url: str, limit: int) -> list[str]:
    """Get article titles using allpages (all articles, main namespace)."""
    titles: list[str] = []
    ap_continue: str | None = None

    async with httpx.AsyncClient(timeout=30.0) as client:
        while len(titles) < limit:
            batch = min(limit - len(titles), 50)
            params: dict = {
                "action": "query",
                "list": "allpages",
                "apnamespace": 0,
                "aplimit": batch,
                "format": "json",
            }
            if ap_continue:
                params["apcontinue"] = ap_continue

            resp = await client.get(base_url, params=params)
            resp.raise_for_status()
            data = resp.json()

            pages = data.get("query", {}).get("allpages", [])
            if not pages:
                break

            titles.extend(p["title"] for p in pages)

            cont = data.get("continue", {}).get("apcontinue")
            if not cont:
                break
            ap_continue = cont

    return titles[:limit]


async def _fetch_category_titles(
    base_url: str, category: str, limit: int
) -> list[str]:
    """Get article titles from a specific category."""
    titles: list[str] = []
    cm_continue: str | None = None

    # Ensure the category has the "Category:" prefix
    if not category.startswith("Category:"):
        category = f"Category:{category}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        while len(titles) < limit:
            batch = min(limit - len(titles), 50)
            params: dict = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": category,
                "cmnamespace": 0,
                "cmlimit": batch,
                "format": "json",
            }
            if cm_continue:
                params["cmcontinue"] = cm_continue

            resp = await client.get(base_url, params=params)
            resp.raise_for_status()
            data = resp.json()

            members = data.get("query", {}).get("categorymembers", [])
            if not members:
                break

            titles.extend(m["title"] for m in members)

            cont = data.get("continue", {}).get("cmcontinue")
            if not cont:
                break
            cm_continue = cont

    return titles[:limit]


async def _fetch_page_contents(
    client: httpx.AsyncClient,
    base_url: str,
    wiki: str,
    titles: list[str],
) -> list[Document]:
    """Fetch full parsed text for a batch of page titles."""
    documents: list[Document] = []

    params = {
        "action": "query",
        "titles": "|".join(titles),
        "prop": "extracts|revisions",
        "explaintext": True,  # plain text, no HTML
        "exsectionformat": "plain",
        "rvprop": "timestamp|user",
        "rvlimit": 1,
        "format": "json",
    }

    resp = await client.get(base_url, params=params)
    resp.raise_for_status()
    data = resp.json()

    pages = data.get("query", {}).get("pages", {})

    for page_id, page in pages.items():
        if int(page_id) < 0:
            # Negative page_id means the page doesn't exist
            continue

        title = page.get("title", "")
        body = page.get("extract", "")

        if not body or len(body.strip()) < 50:
            # Skip stubs / empty pages
            continue

        # Get author from latest revision
        revisions = page.get("revisions", [{}])
        author = revisions[0].get("user", "") if revisions else ""

        documents.append(
            Document(
                id=_make_id(wiki, title),
                title=title,
                body=body,
                author=author,
                created_at=0,
                source="wiki",
            )
        )

    return documents
