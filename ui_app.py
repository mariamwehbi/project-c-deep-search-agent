import streamlit as st
import pandas as pd

from src import (
    scope,
    selector,
    search_links,
    scrape,
    summarize,
    verify,
    export_excel
)

st.set_page_config(page_title="Deep Search & Verification Agent", layout="wide")

st.title("🔍 Deep Search & Verification Agent")
st.write("A simple UI wrapper for the full research pipeline.")

# ---- User Input ----
user_request = st.text_area("Enter your research request:", height=120)

if st.button("Run Deep Search Pipeline"):
    if not user_request.strip():
        st.error("Please enter a research request.")
        st.stop()

    with st.spinner("Clarifying research focus..."):
        focus = scope.clarify_research_focus(user_request)

    st.subheader("🎯 Research Focus")
    st.write(focus)

    with st.spinner("Generating country & strategy list..."):
        records = selector.generate_strategies(focus)

    # Convert to table
    st.subheader("🌍 Generated Strategies")
    strategy_table = pd.DataFrame(
        [[r.country, r.strategy_name] for r in records],
        columns=["Country", "Strategy Name"],
    )
    st.dataframe(strategy_table)

    # ---- Populating Links ----
    with st.spinner("Identifying links using web search..."):
        records = search_links.populate_links(records)

    st.subheader("🔗 Identified Links")
    link_table = pd.DataFrame(
        [[r.country, r.strategy_name, r.primary_link] for r in records],
        columns=["Country", "Strategy", "Primary Link"],
    )
    st.dataframe(link_table)

    # ---- Scrape ----
    with st.spinner("Scraping content..."):
        records = scrape.fetch_all(records)

    # ---- Summaries ----
    with st.spinner("Generating summaries..."):
        records = summarize.summarize_all(records)

    # ---- Verification ----
    with st.spinner("Verifying summaries..."):
        records = verify.verify_all(records)

    # Table for summary & verification
    st.subheader("📝 Summary & Verification Results")
    def _summary_text(s):
    # Try multiple possible attribute names, fall back to str(s)
     return (
        getattr(s, "text",
        getattr(s, "sentence",
        getattr(s, "content", str(s))))
    )

    def _status_text(s):
        return getattr(s, "status", None)

    results_table = pd.DataFrame(
    [
        [
            r.country,
            r.strategy_name,
            r.primary_link,
            "\n".join([_summary_text(s) for s in r.summary_sentences]),
            ", ".join(
                sorted(
                    {st for st in (_status_text(s) for s in r.summary_sentences) if st}
                )
            ),
        ]
        for r in records
    ],
    columns=["Country", "Strategy", "Link", "Summary", "Verification Status"],
)

    st.dataframe(results_table)

    # ---- Export ----
    export_excel.export_to_excel(records)
    st.success("Excel file generated successfully!")
    with open("deep_search_results.xlsx", "rb") as f:
        st.download_button(
            label="⬇️ Download Excel",
            data=f,
            file_name="deep_search_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
