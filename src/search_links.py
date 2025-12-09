from typing import List, Optional

from tavily import TavilyClient
from firecrawl import FirecrawlApp

from .config import TAVILY_API_KEY, FIRECRAWL_API_KEY
from .models import StrategyRecord


tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None
firecrawl_app = FirecrawlApp(api_key=FIRECRAWL_API_KEY) if FIRECRAWL_API_KEY else None


def _choose_best_url(results: List[dict]) -> Optional[str]:

    if not results:
        return None

    # Prefer government / official domains
    preferred_keywords = [
        ".gov", ".gouv", ".go.jp", ".gov.uk", ".gc.ca",
        "transport", "ministry", "govt",
    ]

    for res in results:
        url = res.get("url") or ""
        if any(key in url for key in preferred_keywords):
            return url

    # Fallback: just return the first url with something in it
    for res in results:
        url = res.get("url")
        if url:
            return url

    return None


def _search_with_tavily(query: str) -> Optional[str]:
    if not tavily_client:
        return None

    try:
        response = tavily_client.search(
            query=query,
            max_results=5,
            search_depth="advanced",
        )
        results = response.get("results", [])
        return _choose_best_url(results)
    except Exception as e:
        print(f"[populate_links] Tavily error for query '{query}': {repr(e)}")
        return None


def _search_with_firecrawl(query: str) -> Optional[str]:
    if not firecrawl_app:
        return None

    try:
        resp = firecrawl_app.search(query=query, limit=5)
    except Exception as e:
        print(f"[populate_links] Firecrawl search error for query '{query}': {repr(e)}")
        return None

    # Normalise response into a list of dicts with a 'url' field
    data = []
    if isinstance(resp, dict):
        # Common Firecrawl shape: {"data": [ {...}, {...} ]}
        data = resp.get("data", []) or []
    elif isinstance(resp, list):
        # Some SDKs return a bare list
        data = resp
    else:
        data = []

    results: List[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        # Try common url-like keys
        url = item.get("url") or item.get("link") or item.get("source")
        if url:
            results.append({"url": url})

    return _choose_best_url(results)

def populate_links(records: List[StrategyRecord]) -> List[StrategyRecord]:
    """
    Step 3 in the spec: identify links for each country/strategy.

    Order of attempts per strategy:
    1. Tavily search
    2. Firecrawl search
    3. Deterministic placeholder URL (example.com) as last resort
    """
    for rec in records:
        query = (
            f'"{rec.strategy_name}" {rec.country} national transport strategy official document'
        )

        url = _search_with_tavily(query)

        if not url:
            url = _search_with_firecrawl(query)

        if not url:
            # Last-resort placeholder (clearly marked as such)
            country_slug = rec.country.lower().replace(" ", "-")
            strategy_slug = rec.strategy_name.lower().replace(" ", "-")
            url = f"https://example.com/{country_slug}/{strategy_slug}"

        rec.primary_link = url

    return records
