from typing import List

from firecrawl import FirecrawlApp

from .config import FIRECRAWL_API_KEY
from .models import StrategyRecord

# Only create the client if we actually have a key
firecrawl_app = FirecrawlApp(api_key=FIRECRAWL_API_KEY) if FIRECRAWL_API_KEY else None


def fetch_all(records: List[StrategyRecord]) -> List[StrategyRecord]:
    """
    Step 4 in the spec: fetch raw text for each strategy link.

    - For real URLs, we call Firecrawl's scrape_url and keep the main content.
    - For placeholder/example URLs, we store a clear placeholder message.
    """
    for rec in records:
        url = rec.primary_link or ""

        # If this is obviously a placeholder link, don't pretend it's real
        if "example.com" in url or not firecrawl_app:
            rec.raw_text = (
                f"This is placeholder content for {rec.strategy_name} in {rec.country}. "
                f"In the real implementation, this will contain the scraped content "
                f"from the strategy document at {url or 'a missing URL'}."
            )
            continue

        try:
            result = firecrawl_app.scrape_url(
                url,
                params={"formats": ["markdown"], "onlyMainContent": True},
            )
            markdown = result.get("markdown", "")
            # Avoid huge strings
            rec.raw_text = markdown[:10000] if markdown else (
                f"No main content was extracted from {url}."
            )
        except Exception as e:
            print(f"[fetch_all] Error scraping {url}: {repr(e)}")
            rec.raw_text = (
                f"Could not scrape content for {rec.strategy_name} in {rec.country}. "
                f"Error: {repr(e)}"
            )

    return records
