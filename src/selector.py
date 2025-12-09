from typing import List
from openai import OpenAI

from .config import OPENAI_API_KEY
from .models import StrategyRecord

client = OpenAI(api_key=OPENAI_API_KEY)

PROMPT_TEMPLATE = """
You are a policy research assistant.

Research focus:
{research_focus}

Task:
1. Propose a list of up to 10 countries that are relevant for this research focus.
2. For each country, provide the official or commonly used name of the main national strategy,
   plan, or policy that matches this topic.
3. If you are not sure of the exact official name, create a short descriptive title that a
   researcher could use as a working title (but still realistic).

Output format:
- Return ONLY plain text.
- Each line must be exactly: Country name | Strategy or plan name
- No bullet points, no numbering, no extra commentary, no quotes.

Example:
Germany | National Sustainable Mobility Strategy
Japan | Next-Generation Mobility Strategy
"""


def generate_strategies(research_focus: str) -> List[StrategyRecord]:
    
    if not research_focus:
        research_focus = "National transport and mobility strategies of major economies."

    try:
        prompt = PROMPT_TEMPLATE.format(research_focus=research_focus)

        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions="Generate country and strategy pairs as specified.",
            input=prompt,
        )

        raw_text = (response.output_text or "").strip()
        lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]

        records: List[StrategyRecord] = []
        for line in lines:
            # Expect "Country | Strategy"
            if "|" not in line:
                continue
            country_part, strategy_part = line.split("|", 1)
            country = country_part.strip()
            strategy_name = strategy_part.strip()
            if country and strategy_name:
                records.append(
                    StrategyRecord(
                        country=country,
                        strategy_name=strategy_name,
                    )
                )

        if not records:
            raise ValueError("No valid strategies parsed from model output.")

        return records

    except Exception as e:
        print(f"[generate_strategies] Error calling OpenAI or parsing output: {repr(e)}")
        # Fallback: 2 example strategies
        return [
            StrategyRecord(
                country="Germany",
                strategy_name="National Transport Strategy 2030",
            ),
            StrategyRecord(
                country="Japan",
                strategy_name="Comprehensive Mobility Plan",
            ),
        ]
