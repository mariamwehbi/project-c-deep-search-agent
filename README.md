# Deep Search & Verification Agent – Project C Case Study

This repository contains my implementation of the Deep Search & Verification Agent for Project C.

The feature automates a consultant-style research workflow:

1. Understand the user’s research request and confirm the research focus.
2. Propose a list of countries and strategy names to investigate.
3. Identify authoritative links for each strategy.
4. Scrape the visible content from those links.
5. Generate factual summaries for each strategy.
6. Perform sentence-level verification so every summary statement is backed by evidence.
7. Export all results into a structured Excel file.

Both a command-line interface and a Streamlit UI version are provided.

---

## 1. Workflow Overview

### 1. User Input and Scope Confirmation

- The user provides a free-form research request such as:
  “Research national transportation strategies for the top 10 countries.”
- In CLI mode (`python -m src.main`):
  - The request is clarified with an LLM using `scope.clarify_research_focus()`.
  - The rewritten scope is displayed and the user must approve it.
  - If rejected, the user may revise the scope manually.
- In the Streamlit UI, the clarified scope is displayed beneath the input box.

---

### 2. Strategy Identification (Country + Strategy Name)

- `selector.generate_strategies()` generates a list of suggested country–strategy pairs.
- In CLI mode:
  - A numbered list is shown for user review.
  - The user may remove any entries before confirming the list.
- In the UI version, the list is displayed in a table under “Generated Strategies.”

---

### 3. Link Extraction

Performed in `search_links.populate_links()`.

- Attempts to locate authoritative URLs for each strategy.
- Search behavior is pluggable:
  - Tavily search when available.
  - Optional Firecrawl search.
  - Deterministic placeholder URLs (`example.com/...`) when external APIs fail.
- This ensures the workflow remains fully functional even under rate limits or API key restrictions.
- In CLI mode, the user reviews and approves the link list.
- In the UI, links are displayed under “Identified Links.”

---

### 4. Web Scraping

Implemented in `src/scrape.py`.

- Real URLs are scraped using Firecrawl (HTML → markdown).
- Extracted text is truncated to maintain manageable size.
- Placeholder URLs produce placeholder text so that downstream summarization and verification still run.
- Scraping output becomes the source content used for summarization and verification.

---

### 5. Summary Generation

Implemented in `src/summarize.py`.

- Each strategy's scraped content is summarized into several factual sentences using OpenAI.
- Each sentence is stored as a `SummarySentence` object.
- Summaries are strictly descriptive and avoid subjective rating or interpretation.
- A final descriptive paragraph is generated for Excel export.

---

### 6. Verification Pass (Sentence-Level)

Implemented in `src/verify.py`.

- Every summary sentence is checked against the scraped source text.
- Required verification labels:
  - Verified
  - Partially verified
  - Not verified
- A strategy-level verification status is also computed:
  - All verified
  - Partially verified
  - Not verified
- In CLI mode, the user reviews these results before export.
- In the UI, the user cant review the results or edit them before export.

---

### 7. Excel Assembly

Implemented in `src/export_excel.py`.

- Results are exported to `deep_search_results.xlsx`.
- Required columns:
  - Country
  - Strategy name
  - Description / summary
  - Link
- An additional “Verification status” column is included.
- In the Streamlit UI, a download button is available.

---

## 2. Project Structure

```
project-c-agent/
├─ src/
│  ├─ config.py         # Environment variable loading
│  ├─ models.py         # Data models: StrategyRecord, SummarySentence
│  ├─ scope.py          # LLM-based research focus clarification
│  ├─ selector.py       # Strategy list generation
│  ├─ search_links.py   # Web search and link identification
│  ├─ scrape.py         # Content retrieval
│  ├─ summarize.py      # Summary generation logic
│  ├─ verify.py         # Sentence-level verification engine
│  ├─ export_excel.py   # Excel assembly
│  └─ main.py           # Full CLI workflow
├─ ui_app.py            # Streamlit UI implementation
├─ requirements.txt     # Dependencies
├─ .env                 # API keys (ignored by git)
└─ .gitignore
```

---

## 3. Setup and Installation

### 3.1. Python Environment

This project was developed with Python 3.11.

```
git clone https://github.com/<your-username>/project-c-agent.git
cd project-c-agent

python -m venv project-c-env
project-c-env\Scripts\activate        # Windows PowerShell
# source project-c-env/bin/activate   # macOS / Linux

pip install -r requirements.txt
```

---

### 3.2. Environment Variables

Create a `.env` file:

```
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
FIRECRAWL_API_KEY=your_firecrawl_key
# SERPAPI_API_KEY=your_serpapi_key   (optional)
```

---

## 4. Running the Agent

### 4.1. Command-Line Mode

```
python -m src.main
```

---

### 4.2. Streamlit UI

```
streamlit run ui_app.py
```

---

## 5. Assumptions and Limitations

- Search APIs may be restricted; fallback URLs maintain workflow functionality.
- Scraping supports HTML; PDF parsing is not included.
- Verification operates at sentence level.
- Modular design allows replacing search/scraping components.

---

## 6. Possible Extensions

Some ideas for further improvements (beyond the case requirements):

Pluggable search backends: clean interface to swap between Tavily, SerpAPI, Bing, etc.

Richer UI: a simple “Project C home page” listing multiple features and allowing navigation to this Deep Search agent (aligning with the bonus front-end idea).

Sentence-level Excel sheet: export a second tab with one row per summary sentence and its verification label and evidence span.

Caching: cache search, scraping, and summarization results for repeated runs on the same strategies.

## 7. How This Meets the Evaluation Criteria

Workflow & Logic Clarity (30%)
The pipeline is broken into clear stages with dedicated modules (scope, selector, search_links, scrape, summarize, verify, export_excel) and explicit user approvals in CLI mode.

Technical Feasibility (30%)
The agent runs end-to-end using standard Python tools (OpenAI, Tavily/Firecrawl, pandas, Excel). When external search APIs are limited, deterministic fallbacks keep the workflow functional.

Communication & Structure (20%)
Both CLI and UI flows make intermediate steps visible: research focus, strategy list, links, summaries, and verification overview.

Creativity & Bonus Execution (20%)

Implements a Streamlit UI for interactive usage and Excel download.

Uses a modular design to allow future swapping of web search and scraping backends.

Provides verification labels to reduce hallucination risk and support evidence-based analysis.
