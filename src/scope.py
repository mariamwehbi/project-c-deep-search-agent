# src/scope.py

from openai import OpenAI
from .config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def clarify_research_focus(user_request: str) -> str:
    """
    Takes the user's free-text request and returns a single, clear
    research focus sentence.

    This is Step 1 in the spec: "User submits a research request"
    and the system interprets & clarifies the scope.
    """
    user_request = (user_request or "").strip()
    if not user_request:
        return (
            "Provide an overview of national public transport and mobility strategies "
            "for major economies."
        )

    prompt = f"""
You are a research assistant helping a consultant.

The user wrote this research request:

\"\"\"{user_request}\"\"\"

Rewrite this as ONE clear, concise "research focus" sentence that could be used as a brief.
It should:
- mention the topic,
- specify the main angle (e.g. comparison, overview, impact),
- avoid unnecessary fluff.

Output format:
Return ONLY the final sentence, no bullet points, no quotes, no explanation.
"""

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions="Rewrite the request as a single clear research focus sentence.",
            input=prompt,
        )
        focus = (response.output_text or "").strip()
        # Safety fallback
        return focus or user_request
    except Exception as e:
        print(f"[clarify_research_focus] Error calling OpenAI: {repr(e)}")
        return user_request
