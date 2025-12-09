import pandas as pd
from typing import List
from .models import StrategyRecord

def export_to_excel(records: List[StrategyRecord], path: str = "deep_search_results.xlsx"):
    rows = []
    for rec in records:
        # Sentences we keep in the description
        verified_sentences = [
            s.sentence for s in rec.summary_sentences
            if s.status in (None, "Verified", "Partially verified")
        ]
        description = " ".join(verified_sentences)

        # Overall verification status for this strategy
        if not rec.summary_sentences:
            overall_status = "No summary"
        else:
            statuses = {s.status for s in rec.summary_sentences}
            if statuses == {"Verified"}:
                overall_status = "All verified"
            elif "Not verified" in statuses:
                overall_status = "Contains unverified sentences"
            else:
                overall_status = "Partially verified"

        rows.append({
            "Country": rec.country,
            "Strategy name": rec.strategy_name,
            "Description / summary": description,
            "Link": rec.primary_link or "",
            "Verification status": overall_status,
        })

    df = pd.DataFrame(rows)
    df.to_excel(path, index=False)
