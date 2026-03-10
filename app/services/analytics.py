"""In-memory search analytics tracking service."""

import threading
from collections import Counter
from datetime import datetime, timezone

from app.models.analytics import (
    AnalyticsSummary,
    ModeBreakdown,
    QueryRecord,
    TopQuery,
)


class SearchAnalytics:
    """Thread-safe in-memory analytics tracker."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: list[dict] = []

    def record(
        self, query: str, mode: str, total_found: int, latency_ms: float
    ) -> None:
        """Record a search event."""
        with self._lock:
            self._records.append(
                {
                    "query": query.lower().strip(),
                    "mode": mode,
                    "total_found": total_found,
                    "latency_ms": round(latency_ms, 2),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

    def get_summary(self, top_n: int = 10, recent_n: int = 20) -> AnalyticsSummary:
        """Compute aggregate analytics."""
        with self._lock:
            records = list(self._records)

        total = len(records)
        if total == 0:
            return AnalyticsSummary(
                total_searches=0,
                unique_queries=0,
                avg_latency_ms=0.0,
                top_queries=[],
                mode_breakdown=[],
                recent_searches=[],
                searches_over_time={},
            )

        # Unique queries
        query_counter = Counter(r["query"] for r in records)
        unique = len(query_counter)

        # Average latency
        avg_lat = sum(r["latency_ms"] for r in records) / total

        # Top queries
        top_queries = [
            TopQuery(query=q, count=c)
            for q, c in query_counter.most_common(top_n)
        ]

        # Mode breakdown
        mode_counter = Counter(r["mode"] for r in records)
        mode_breakdown = [
            ModeBreakdown(
                mode=m,
                count=c,
                percentage=round(c / total * 100, 1),
            )
            for m, c in mode_counter.most_common()
        ]

        # Recent searches
        recent = [
            QueryRecord(**r)
            for r in reversed(records[-recent_n:])
        ]

        # Searches per day
        day_counter: Counter = Counter()
        for r in records:
            day = r["timestamp"][:10]  # YYYY-MM-DD
            day_counter[day] += 1
        searches_over_time = dict(sorted(day_counter.items()))

        return AnalyticsSummary(
            total_searches=total,
            unique_queries=unique,
            avg_latency_ms=round(avg_lat, 2),
            top_queries=top_queries,
            mode_breakdown=mode_breakdown,
            recent_searches=recent,
            searches_over_time=searches_over_time,
        )


# Module-level singleton
analytics = SearchAnalytics()
