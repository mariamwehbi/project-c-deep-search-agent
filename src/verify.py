from typing import List

from openai import OpenAI
from .config import OPENAI_API_KEY
from .models import StrategyRecord, SummarySentence


client = OpenAI(api_key=OPENAI_API_KEY)

VERIFY_PROMPT_TEMPLATE = """
You are a strict fact-checking assistant.

Country: {country}
Strategy name: {strategy_name}

Extracted text from the strategy:
\"\"\"{text}\"\"\"

Summary sentences to verify:
{sentences_block}

Task:
For each summary sentence, judge whether it is:

- "Verified"          → fully supported by the text
- "Partially verified"→ some parts supported, some unclear
- "Not verified"      → not supported or contradicted by the text

Rules:
- Do NOT be generous. If the text does not clearly support the sentence, mark it
  as Partially verified or Not verified.
- Ignore your prior knowledge; use ONLY the provided text.

Output format:
Return ONLY plain text.
Output exactly one line per sentence, in the same order, with this format:

STATUS | very short reason

Where STATUS is one of:
- Verified
- Partially verified
- Not verified

Example:
Verified | goal clearly stated in the first paragraph
Partially verified | funding is mentioned but no amount
Not verified | no evidence of timeline in the text
"""


def verify_all(records: List[StrategyRecord]) -> List[StrategyRecord]:
    """
    Use GPT-4.1-mini to assign a verification status to each summary sentence.
    Falls back to 'Partially verified' if anything goes wrong.
    """
    for rec in records:
        if not rec.raw_text or not rec.summary_sentences:
            continue

        sentences_block = "\n".join(
            f"{idx+1}. {s.sentence}" for idx, s in enumerate(rec.summary_sentences)
        )

        try:
            prompt = VERIFY_PROMPT_TEMPLATE.format(
                country=rec.country,
                strategy_name=rec.strategy_name,
                text=rec.raw_text[:8000],
                sentences_block=sentences_block,
            )

            response = client.responses.create(
                model="gpt-4.1-mini",
                instructions=(
                    "Fact-check each summary sentence strictly against the text and "
                    "output one STATUS line per sentence as specified."
                ),
                input=prompt,
            )

            raw = (response.output_text or "").strip()
            lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]

            # Match each summary sentence with a status line
            for sent_obj, line in zip(rec.summary_sentences, lines):
                # STATUS is before the first '|'
                status_token = line.split("|", 1)[0].strip()
                if status_token not in {"Verified", "Partially verified", "Not verified"}:
                    status_token = "Partially verified"
                sent_obj.status = status_token

            # For any leftover sentences (if model returned fewer lines), set default
            for sent_obj in rec.summary_sentences[len(lines):]:
                if not sent_obj.status:
                    sent_obj.status = "Partially verified"

        except Exception as e:
            print(f"[verify_all] Error verifying {rec.country}: {repr(e)}")
            # Conservative fallback: mark as partially verified
            for s in rec.summary_sentences:
                if not s.status:
                    s.status = "Partially verified"

    return records
