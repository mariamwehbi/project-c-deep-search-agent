import pandas as pd
from typing import List
from .models import StrategyRecord

def export_to_excel(records: List[StrategyRecord], path: str = "deep_search_results.xlsx"):
    rows = []

    for rec in records:

        # --- Build FULL summary (all sentences joined) ---
        description = " ".join([s.sentence for s in rec.summary_sentences])

        # --- Compute overall verification status ---
        if not rec.summary_sentences:
            overall_status = "Not verified"
        else:
            statuses = {s.status for s in rec.summary_sentences if s.status}

            if statuses == {"Verified"}:
                overall_status = "Verified"
            elif statuses == {"Not verified"}:
                overall_status = "Not verified"
            else:
                # mixture: Verified + Partially verified or includes some Not verified
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
