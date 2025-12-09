from typing import List

from . import (
    scope,
    selector,
    search_links,
    scrape,
    summarize,
    verify,
    export_excel,
)
from .models import StrategyRecord


def ask_yes_no(prompt: str) -> bool:
    """Simple y/n approval helper."""
    while True:
        answer = input(f"{prompt} [y/n]: ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please answer with 'y' or 'n'.")


def approve_or_edit_strategies(records: List[StrategyRecord]) -> List[StrategyRecord]:
    """Show the proposed country/strategy list and allow basic edits (removals)."""
    print("\n>>> Proposed country & strategy list:")
    for idx, rec in enumerate(records, start=1):
        print(f"{idx:2d}. {rec.country} – {rec.strategy_name}")

    # Allow user to remove entries by number
    to_remove = input(
        "\nIf you want to remove any entries, type their numbers separated by commas "
        "(or press Enter to keep all): "
    ).strip()

    if to_remove:
        try:
            remove_indices = {
                int(x.strip()) for x in to_remove.split(",") if x.strip().isdigit()
            }
            records = [
                rec for idx, rec in enumerate(records, start=1)
                if idx not in remove_indices
            ]
        except Exception:
            print("Could not parse removal list, keeping all entries.")

    # Final approval
    print("\n>>> Final country & strategy list:")
    for idx, rec in enumerate(records, start=1):
        print(f"{idx:2d}. {rec.country} – {rec.strategy_name}")

    if not ask_yes_no("\nDo you approve this list and want to proceed?"):
        print("Stopping workflow before scraping / summarization.")
        return []

    return records


def run_pipeline(user_request: str) -> None:
    print(">>> Starting pipeline...")

    # 1) SCOPE CLARIFICATION + APPROVAL (Step 1 in spec)
    research_focus = scope.clarify_research_focus(user_request)
    print(f"\nResearch focus: {research_focus}")

    if not ask_yes_no("Do you approve this research focus?"):
        # Allow user to type their own exact focus instead of aborting entirely
        manual = input(
            "Please type the exact research focus you'd like to use "
            "(or leave blank to cancel): "
        ).strip()
        if not manual:
            print("No research focus provided. Exiting.")
            return
        research_focus = manual
        print(f"\nUsing manual research focus: {research_focus}")

    # 2) GENERATE COUNTRY + STRATEGY LIST (Step 2) + APPROVAL/EDIT
    records: List[StrategyRecord] = selector.generate_strategies(research_focus)
    if not records:
        print("No strategies were generated. Exiting.")
        return

    records = approve_or_edit_strategies(records)
    if not records:
        return  # user chose to stop

    # 3) LINK EXTRACTION (Step 3) – user review/approval (simple yes/no)
    records = search_links.populate_links(records)
    print("\n>>> Links identified (showing primary link per country):")
    for rec in records:
        print(f"- {rec.country}: {rec.primary_link}")

    if not ask_yes_no(
        "\nDo you approve these links and want to proceed to scraping and summarization?"
    ):
        print("Stopping workflow before scraping.")
        return

    # 4) SCRAPING (Step 4)
    records = scrape.fetch_all(records)
    print("\nRaw text fetched for all approved links.")

    # 5) SUMMARY GENERATION (Step 5)
    records = summarize.summarize_all(records)
    print("Summaries created.")

    # 6) VERIFICATION (Step 6) + FINAL APPROVAL
    records = verify.verify_all(records)
    print("Verification completed.")

    # Quick console summary for user review
    print("\n>>> Verification overview:")
    for rec in records:
        statuses = {s.status for s in rec.summary_sentences if s.status}
        status_display = ", ".join(sorted(statuses)) or "unknown"
        print(f"- {rec.country}: {status_display}")

    if not ask_yes_no(
        "\nDo you approve these summaries and verification results to be exported to Excel?"
    ):
        print("User did not approve final summaries. Exiting without export.")
        return

    # 7) EXCEL EXPORT (Step 7)
    export_excel.export_to_excel(records)
    print("Exported deep_search_results.xlsx")


if __name__ == "__main__":
    user_prompt = input("\nEnter your research request: ")
    run_pipeline(user_prompt)
