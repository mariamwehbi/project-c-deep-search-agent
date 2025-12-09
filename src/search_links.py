from typing import List, Optional
from urllib.parse import urlparse

import requests
from tavily import TavilyClient
from firecrawl import FirecrawlApp

from .config import TAVILY_API_KEY, FIRECRAWL_API_KEY, SERPAPI_API_KEY
from .models import StrategyRecord


tavily_client: Optional[TavilyClient] = (
    TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None
)

firecrawl_app: Optional[FirecrawlApp] = (
    FirecrawlApp(api_key=FIRECRAWL_API_KEY) if FIRECRAWL_API_KEY else None
)


def _search_with_serpapi(query: str) -> List[str]:
    """Search using SerpAPI and return a list of URLs (best-effort)."""
    if not SERPAPI_API_KEY:
        return []

    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "num": 10,
    }

    try:
        resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        urls: List[str] = []
        for r in data.get("organic_results", []):
            url = r.get("link")
            if url:
                urls.append(url)
        return urls
    except Exception as e:
        print(f"[populate_links] SerpAPI error for query '{query}': {repr(e)}")
        return []


def _search_with_tavily(query: str) -> List[str]:
    if not tavily_client:
        return []
    try:
        res = tavily_client.search(query, max_results=8)
        return [r["url"] for r in res.get("results", []) if r.get("url")]
    except Exception as e:
        print(f"[populate_links] Tavily error for query '{query}': {repr(e)}")
        return []


def _search_with_firecrawl(query: str) -> List[str]:
    if not firecrawl_app:
        return []
    try:
        res = firecrawl_app.search(query, params={"limit": 8})
        return [r["url"] for r in res.get("data", []) if r.get("url")]
    except Exception as e:
        print(f"[populate_links] Firecrawl search error for query '{query}': {repr(e)}")
        return []


def _choose_best_url(urls: List[str]) -> Optional[str]:
    """Prefer official / government looking domains if possible."""
    if not urls:
        return None

    def score(url: str) -> int:
        host = urlparse(url).netloc.lower()
        s = 0
        # Prefer government / official domains
        if any(x in host for x in ["gov", "gouv", ".gc.ca", ".go.jp", ".go.kr"]):
            s += 2
        if "transport" in host or "mobility" in host or "infrastructure" in host:
            s += 1
        return s

    return sorted(urls, key=score, reverse=True)[0]


def _fallback_placeholder(rec: StrategyRecord) -> str:
    """Last resort deterministic placeholder so the pipeline still runs."""
    slug_country = rec.country.lower().replace(" ", "-")
    slug_strategy = rec.strategy_name.lower().replace(" ", "-")
    return f"https://example.com/{slug_country}/{slug_strategy}"


def populate_links(records: List[StrategyRecord]) -> List[StrategyRecord]:
    """
    For each (country, strategy) record:
    - Use SerpAPI to search for the official or authoritative URL
    - Fall back to Tavily, then Firecrawl search
    - If all fail, use a deterministic placeholder URL
    """

    for rec in records:
        query = (
            f'"{rec.strategy_name}" {rec.country} '
            f"national transport OR mobility strategy official document"
        )

        all_candidates: List[str] = []

        # 1) SerpAPI (primary)
        all_candidates.extend(_search_with_serpapi(query))

        # 2) Tavily (fallback)
        if not all_candidates:
            all_candidates.extend(_search_with_tavily(query))

        # 3) Firecrawl search (fallback)
        if not all_candidates:
            all_candidates.extend(_search_with_firecrawl(query))

        # 4) Choose best + secondaries, or placeholder
        if all_candidates:
            best = _choose_best_url(all_candidates) or all_candidates[0]
            rec.primary_link = best
            rec.secondary_links = [
                u for u in all_candidates if u != best
            ][:3]  # up to 3 secondaries
        else:
            rec.primary_link = _fallback_placeholder(rec)
            rec.secondary_links = []

        # Helpful for CLI logging
        print(
            f"[populate_links] {rec.country}: "
            f"{rec.strategy_name} -> {rec.primary_link}"
        )

    return records
