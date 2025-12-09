from typing import List
import pandas as pd

from .models import StrategyRecord


# Max words we allow in the summary sentence
MAX_WORDS = 30


def _short_one_sentence(text: str, max_words: int = MAX_WORDS) -> str:
    """
    Take the full joined summary text and compress it into ONE short sentence.

    Steps:
    1. Take everything up to the first period '.' if it exists.
    2. If that sentence is still too long, cut it to `max_words` and add a period.
    """
    if not text:
        return ""

    # 1) Cut at the first period if present.
    first_period = text.find(".")
    if first_period != -1:
        candidate = text[: first_period + 1]
    else:
        candidate = text

    candidate = candidate.strip()

    # 2) Hard cap on number of words.
    words = candidate.split()
    if len(words) > max_words:
        candidate = " ".join(words[:max_words]).rstrip(".,;:") + "."

    return candidate.strip()


def export_to_excel(records: List[StrategyRecord], path: str = "deep_search_results.xlsx") -> None:
    rows = []

    for rec in records:
        # Join all (verified / partially verified) sentences into one big string
        # then compress to a single sentence.
        all_sentences = [
            s.sentence
            for s in rec.summary_sentences
            if s.status in (None, "Verified", "Partially verified")
        ]
        joined = " ".join(all_sentences).strip()
        description = _short_one_sentence(joined)

        # --- Overall verification status per strategy (strict 3-class) ---
        if not rec.summary_sentences:
            overall_status = "Not verified"
        else:
            statuses = {s.status for s in rec.summary_sentences if s.status is not None}

            if not statuses:
                # If nothing was explicitly labelled, treat as Verified to avoid "weird" states
                overall_status = "Verified"
            elif statuses == {"Verified"}:
                overall_status = "Verified"
            elif statuses == {"Not verified"}:
                overall_status = "Not verified"
            else:
                # any mix of Verified / Partially verified / Not verified
                overall_status = "Partially verified"

        rows.append(
            {
                "Country": rec.country,
                "Strategy name": rec.strategy_name,
                "Description / summary": description,
                "Link": rec.primary_link or "",
                "Verification status": overall_status,
            }
        )

    df = pd.DataFrame(rows)
    df.to_excel(path, index=False)
