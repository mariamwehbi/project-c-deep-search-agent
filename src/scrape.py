from typing import List
from io import BytesIO

import requests
import pdfplumber
from bs4 import BeautifulSoup

from .models import StrategyRecord


def _extract_pdf_text(content: bytes, max_pages: int = 5) -> str:
    """
    Extract text from a PDF byte stream.
    To keep things fast, only the first `max_pages` pages are processed.
    """
    text_chunks = []
    with pdfplumber.open(BytesIO(content)) as pdf:
        for i, page in enumerate(pdf.pages):
            if i >= max_pages:
                break
            page_text = page.extract_text() or ""
            text_chunks.append(page_text)
    return "\n".join(text_chunks)


def _extract_html_text(html: str) -> str:
    """Extract visible text from an HTML page."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove common noise
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    body = soup.body or soup
    text = body.get_text(separator="\n", strip=True)
    return text


def _fetch_url_text(url: str) -> str:
    """
    Fetch and extract text from a URL.
    - If PDF: use pdfplumber
    - Else: treat as HTML
    On any error (403, timeout, etc.), return a clear placeholder string.
    """
    try:
        resp = requests.get(url, timeout=25)

        # If server returns an error code, don't crash – just log & fallback
        if resp.status_code >= 400:
            print(f"[fetch_all] HTTP {resp.status_code} for {url}")
            return (
                "No readable content could be extracted from this URL due to "
                f"an HTTP error ({resp.status_code}). This is a placeholder description."
            )

        content_type = resp.headers.get("Content-Type", "").lower()

        # PDF by extension or content-type
        if url.lower().endswith(".pdf") or "application/pdf" in content_type:
            return _extract_pdf_text(resp.content)

        # Otherwise, assume HTML
        return _extract_html_text(resp.text)

    except Exception as e:
        print(f"[fetch_all] Error scraping {url}: {repr(e)}")
        return (
            "No readable content could be extracted from this URL. "
            "This is a placeholder description based on the link only."
        )


def fetch_all(records: List[StrategyRecord]) -> List[StrategyRecord]:
    """
    For each StrategyRecord:
      - If the link is a fake example.com placeholder, explain that.
      - Otherwise, fetch the URL and extract readable text.
    """
    for rec in records:
        url = rec.primary_link or ""

        if not url:
            rec.raw_text = (
                f"No link is available for {rec.strategy_name} in {rec.country}."
            )
            continue

        # If it's one of our deterministic placeholders, be explicit
        if "example.com" in url:
            rec.raw_text = (
                f"This is a placeholder link (example.com) for "
                f"{rec.strategy_name} in {rec.country}. "
                "No official document could be reliably located by the search step."
            )
            continue

        # Real URL → try to scrape
        rec.raw_text = _fetch_url_text(url)

        # Trim to avoid enormous strings
        if len(rec.raw_text) > 15000:
            rec.raw_text = rec.raw_text[:15000]

    return records
