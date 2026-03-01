"""Reddit data fetcher — pulls posts from any subreddit."""

import httpx
from app.config import get_settings
from app.models.document import Document


async def fetch_posts(
    subreddit: str = "minecraft",
    limit: int = 50,
    sort: str = "hot",
) -> list[Document]:
    """Fetch posts from Reddit's public JSON API.

    Args:
        subreddit: Name of the subreddit (without r/).
        limit: Number of posts to fetch (max 100 per request, uses pagination).
        sort: Sorting mode — "hot", "new", or "top".

    Returns:
        A list of Document models.
    """
    s = get_settings()
    documents: list[Document] = []
    after: str | None = None
    remaining = limit

    async with httpx.AsyncClient() as client:
        while remaining > 0:
            batch = min(remaining, 100)
            url = f"https://www.reddit.com/r/{subreddit}/{sort}.json"
            params: dict = {"limit": batch, "raw_json": 1}
            if after:
                params["after"] = after

            resp = await client.get(
                url,
                params=params,
                headers={"User-Agent": s.reddit_user_agent},
                follow_redirects=True,
            )
            resp.raise_for_status()
            data = resp.json()

            children = data.get("data", {}).get("children", [])
            if not children:
                break

            for item in children:
                d = item["data"]
                documents.append(
                    Document(
                        id=d["id"],
                        title=d.get("title", ""),
                        body=d.get("selftext", ""),
                        author=d.get("author", ""),
                        created_at=int(d.get("created_utc", 0)),
                        source="reddit",
                    )
                )

            after = data.get("data", {}).get("after")
            if not after:
                break
            remaining -= len(children)

    return documents[:limit]
