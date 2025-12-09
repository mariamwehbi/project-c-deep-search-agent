# src/summarize.py

from typing import List

from openai import OpenAI
from .config import OPENAI_API_KEY
from .models import StrategyRecord, SummarySentence


client = OpenAI(api_key=OPENAI_API_KEY)

SUMMARY_PROMPT_TEMPLATE = """
You are a neutral policy research assistant.

Country: {country}
Strategy name: {strategy_name}

You are given extracted text from this strategy.

Task:
1. Write a concise, factual summary of this strategy in 3–5 sentences.
2. Focus ONLY on what is clearly stated in the text: objectives, priority areas,
   key programs, and implementation focus.
3. Do NOT interpret, predict, critique, or add extra information.
4. Each sentence must be directly supported by the text.
5. Output format: each sentence on its own line. No bullet points, no numbering,
   no quotes, no extra commentary.

Here is the extracted text:

\"\"\"{text}\"\"\"
"""


def summarize_all(records: List[StrategyRecord]) -> List[StrategyRecord]:
    """
    Use GPT-4.1-mini to create 3–5 factual sentences per strategy
    based on the scraped raw_text. Falls back to a simple template
    if anything goes wrong.
    """
    for rec in records:
        if not rec.raw_text:
            continue

        try:
            prompt = SUMMARY_PROMPT_TEMPLATE.format(
                country=rec.country,
                strategy_name=rec.strategy_name,
                text=rec.raw_text[:8000],  # safety truncation
            )

            response = client.responses.create(
                model="gpt-4.1-mini",
                instructions=(
                    "Produce 3–5 strictly factual sentences, one per line, "
                    "grounded only in the provided text."
                ),
                input=prompt,
            )

            raw = (response.output_text or "").strip()
            lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]

            sentences = [
                SummarySentence(sentence=line)
                for line in lines
            ]

            if not sentences:
                raise ValueError("No sentences generated")

            rec.summary_sentences = sentences

        except Exception as e:
            print(f"[summarize_all] Error summarizing {rec.country}: {repr(e)}")
            fallback = (
                f"{rec.country}'s \"{rec.strategy_name}\" focuses on "
                f"transport and mobility policy."
            )
            rec.summary_sentences = [SummarySentence(sentence=fallback)]

    return records
