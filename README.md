# Deep Search & Verification Agent – Project C Case Study

This repository contains my implementation of the **Deep Search & Verification Agent** for Project C.

The goal of this feature is to automate a consultant-style research workflow:

1. Understand the user’s research request and confirm the **research focus**.
2. Propose a list of **countries + strategy names** to investigate.
3. Find **authoritative links** for each strategy.
4. **Scrape** the visible content from those links.
5. Generate **factual summaries** of each strategy.
6. Perform **sentence-level verification** so every summary sentence is backed by evidence.
7. Export the results into a clean **Excel file** that can be used for benchmarking.

The agent can be run either from the **command line** or via a simple **Streamlit web UI**.

---

## 1. How the Workflow Maps to the Assignment

### 1. User Input & Scope Confirmation

- The user starts by entering a free-form request, e.g.:

  > “Research national transportation strategies for the top 10 countries”

- In **CLI mode** (`python -m src.main`), the agent:
  - Calls `scope.clarify_research_focus()` (using OpenAI) to rewrite the request into a clear research focus.
  - Shows the proposed focus and asks:  
    `Do you approve this research focus? [y/n]`
  - If the user answers `n`, they can type their own focus string.

- In the **Streamlit UI** (`streamlit run ui_app.py`), the clarified research focus is displayed immediately below the input so the user can visually confirm the scope.

### 2. Strategy Identification (Countries + Strategy Names)

- `selector.generate_strategies()` uses the research focus to propose a list of **countries** and **strategy names** (e.g., national transport or mobility strategies).
- In **CLI mode**, the user sees a numbered list and can remove entries:

  ```text
  >>> Proposed country & strategy list:
   1. United States – National Freight Strategic Plan
   2. China – National Transport Development Strategy
   ...
  If you want to remove any entries, type their numbers separated by commas (or press Enter to keep all):

After editing, the user must confirm:

Do you approve this list and want to proceed? [y/n]

In the UI, the same list is shown in a table under “Generated Strategies”.

These records are represented by the StrategyRecord dataclass in src/models.py.

### 3. Link Extraction (Search Stage)

search_links.populate_links() is responsible for finding links for each (country, strategy).

The search logic is designed to be pluggable:

First attempts a web search using Tavily (if available).

Optionally can use Firecrawl search as a fallback (for environments where that’s configured).

If both fail (e.g., API key issues or rate limits), the code falls back to deterministic placeholder URLs on example.com.
This allows the rest of the pipeline (scraping, summarization, verification, Excel export) to run consistently even when search APIs are restricted during the case study.

In CLI mode, a summary of the primary link per country is shown and the user is asked:

Do you approve these links and want to proceed to scraping and summarization? [y/n]

In the UI, the “Identified Links” table shows the Country, Strategy, and Primary Link columns.

Note: In a real production setting, the placeholder URLs would be replaced once a stable search provider (e.g., Tavily, SerpAPI, or Bing Web Search) is configured.

### 4. Web Scraping

Implemented in src/scrape.py via fetch_all(records).

Current version uses Firecrawl where possible:

For non-placeholder URLs, FirecrawlApp.scrape_url() is called with onlyMainContent=True and markdown format.

Extracted markdown is truncated to a safe length to avoid huge payloads.

For placeholder URLs (example.com), the scraper injects a clear placeholder text explaining that this is synthetic content.
This keeps the pipeline functional under limited API access while still demonstrating the scraping and verification logic.

### 5. Summary Generation

src/summarize.py runs the summarization step via summarize_all(records).

For each strategy:

The scraped raw text is split and passed to an OpenAI call.

The model returns a set of structured summary sentences, each with:

country

strategy_name

sentence (the actual sentence text)

Sentences are stored as SummarySentence objects on the corresponding StrategyRecord.

The final summary for Excel is the concatenation of these sentences into one descriptive paragraph:

Descriptive, not interpretive: Focus on objectives, pillars, timelines, and relevant scope.

No ranking or subjective evaluation is added.

### 6. Verification Pass (Sentence-Level)

Implemented in src/verify.py via verify_all(records).

For each SummarySentence:

The agent checks whether the sentence (or its core facts) are supported by the scraped raw_text.

Each sentence receives a verification_status label, one of:

"Verified" – sentence is fully supported by the source.

"Partially verified" – most of the sentence matches, but some elements are weak or only indirectly stated.

"Not verified" – the claim does not appear or cannot be backed by the scraped content.

For each strategy, the code also computes an overall verification_status:

"All verified" – every sentence is verified.

"Partially verified" – some sentences are partially or not verified.

"Not verified" – none of the sentences could be verified.

In CLI mode, a short verification overview is printed:

>>> Verification overview:
- Germany: All verified
- Japan: Partially verified
...

In the UI, the “Summary & Verification Results” table shows each row with:

Country

Strategy

Link

Full summary (joined sentences)

Aggregated verification status

The user is then asked in CLI mode:

Do you approve these summaries and verification results to be exported to Excel? [y/n]

### 7. Excel Assembly

Implemented in src/export_excel.py.

The final Excel file is named: deep_search_results.xlsx and is written to the project root.

Required columns (per the assignment) are included:

Country

Strategy name

Description / summary

Link

Additionally, an extra column is added:

Verification status – the overall status per strategy (All verified, Partially verified, or Not verified).

In the Streamlit UI, a Download button is provided to download the Excel file directly.

## 2. Project Structure
project-c-agent/
├─ src/
│  ├─ config.py         # Loads API keys from .env
│  ├─ models.py         # Dataclasses: StrategyRecord, SummarySentence
│  ├─ scope.py          # Clarifies research focus using LLM
│  ├─ selector.py       # Generates (country, strategy) list
│  ├─ search_links.py   # Web search & link selection (Tavily / Firecrawl / fallbacks)
│  ├─ scrape.py         # Scrapes text content via Firecrawl (with placeholders)
│  ├─ summarize.py      # Creates factual summaries and sentence objects
│  ├─ verify.py         # Sentence-level verification & aggregate status
│  ├─ export_excel.py   # Builds deep_search_results.xlsx
│  └─ main.py           # CLI entrypoint and end-to-end pipeline orchestration
├─ ui_app.py            # Streamlit UI wrapper
├─ requirements.txt     # Python dependencies
├─ .env                 # Environment variables (NOT checked into git)
└─ .gitignore

## 3. Setup & Installation
### 3.1. Python Environment

Tested with Python 3.11.
# Clone the repo
git clone https://github.com/<your-username>/project-c-agent.git
cd project-c-agent

# Create and activate a virtual environment (optional but recommended)
python -m venv project-c-env
project-c-env\Scripts\activate       # Windows PowerShell
# source project-c-env/bin/activate  # macOS / Linux

# Install dependencies
pip install -r requirements.txt

### 3.2. Environment Variables

Create a .env file in the project root:
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=your_tavily_key_here          # optional / used when available
FIRECRAWL_API_KEY=your_firecrawl_key_here    # used for scraping
#SERPAPI_API_KEY=your_serpapi_key_here      # optional future extension

Keys are loaded in src/config.py via python-dotenv.

.env is already ignored by .gitignore so that API keys are not exposed in the repository.

## 4. Running the Agent
### 4.1. Command-Line Mode

From the project root (with the virtualenv activated):
python -m src.main

You will be prompted for:

Research request

Confirmation of research focus

Approval / editing of the country & strategy list

Approval of identified links

Approval of final summaries & verification before export

The final Excel file deep_search_results.xlsx will be created in the project root.

### 4.2. Streamlit Web UI

streamlit run ui_app.py

The UI provides:

A text area for the research request.

A display of the Research Focus.

Tables for:

Generated Strategies

Identified Links

Summary & Verification Results

A Download Excel button once the run is complete.

This satisfies the bonus “simple UI” requirement in the case description.

## 5. Assumptions & Limitations

Search providers:
During the case, external web search APIs may be rate-limited or blocked.
To keep the workflow stable, search_links.py is written to:

Try Tavily first (when authorized).

Optionally use Firecrawl search.

Fall back to deterministic example.com URLs if all web search options fail.

This allows the rest of the pipeline (scraping, summarization, verification, Excel export) to be demonstrated consistently. With a working SerpAPI / Bing / Tavily key, these placeholders can be replaced by real government URLs without changing the overall logic.

Scraping:
Current scraping is optimized for HTML pages via Firecrawl and simple placeholder text. For real production use, PDF parsing and richer error handling would be added.

Verification granularity:
Verification happens at sentence level and returns one of Verified, Partially verified, Not verified.
The Excel export aggregates these into a single Verification status per strategy.
If a more detailed audit trail is required, an additional sheet with sentence-level breakdown could be added.

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

