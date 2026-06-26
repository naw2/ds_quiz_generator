"""generate_question.py — Use the Claude API to create a new quiz question
for a specific topic (used to target a student's weak areas).

Uses the teacher-provided proxy at proxy.vibecode.tours.
Does NOT use the Anthropic SDK — uses plain HTTP (urllib) because
the proxy needs a different auth method than what the SDK sends.
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# Try to get settings from Streamlit secrets first, then env vars
try:
    import streamlit as st
    API_KEY = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY")
    BASE_URL = os.getenv("ANTHROPIC_BASE_URL") or st.secrets.get("ANTHROPIC_BASE_URL", "https://proxy.vibecode.tours")
    MODEL = os.getenv("ANTHROPIC_MODEL") or st.secrets.get("ANTHROPIC_MODEL", "mimo-v2.5-pro")
except Exception:
    # Fallback if not running in Streamlit
    API_KEY = os.getenv("ANTHROPIC_API_KEY")
    BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "https://proxy.vibecode.tours")
    MODEL = os.getenv("ANTHROPIC_MODEL", "mimo-v2.5-pro")


def call_claude(prompt):
    """Send a prompt to Claude via the proxy and return the text response.

    Uses the requests library for HTTP calls.
    The teacher's proxy expects:
      - Authorization: Bearer header for authentication
      - model: mimo-v2.5-pro
    """
    url = f"{BASE_URL}/v1/messages"

    body = {
        "model": MODEL,
        "max_tokens": 1000,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }

    # Retry up to 3 times (the proxy can be flaky)
    last_error = None
    for attempt in range(1, 4):
        try:
            response = requests.post(url, headers=headers, json=body, timeout=30)

            if response.status_code == 502:
                # Bad gateway — proxy is down momentarily, wait and retry
                last_error = f"502 Bad Gateway (attempt {attempt})"
                import time
                time.sleep(2)
                continue

            if not response.ok:
                raise RuntimeError(f"API error {response.status_code}: {response.text}")

            data = response.json()

            # The proxy returns content blocks — find the "text" block
            for block in data.get("content", []):
                if block.get("type") == "text":
                    text = block["text"]
                    if text and text.strip():
                        return text

            # Fallback: try the first content block's text
            first_text = data["content"][0].get("text", "")
            if first_text and first_text.strip():
                return first_text

            last_error = f"Empty response from API (attempt {attempt})"

        except RuntimeError:
            raise  # re-raise non-retryable errors immediately
        except Exception as e:
            last_error = str(e)
            import time
            time.sleep(1.5)

    raise RuntimeError(f"Failed after 3 attempts: {last_error}")


def generate_question(topic):
    """Ask Claude to create ONE new multiple-choice question on `topic`.

    Returns a dictionary in the SAME shape as our hardcoded questions:
    {"question": ..., "options": {...}, "answer": ..., "topic": ...}
    """

    prompt = f"""Create one multiple-choice Python question for a beginner
data science student, about the topic: {topic}.

Reply with ONLY valid JSON, no other text, no markdown formatting,
in exactly this shape:

{{
  "question": "the question text",
  "options": {{
    "A": "option A text",
    "B": "option B text",
    "C": "option C text",
    "D": "option D text"
  }},
  "answer": "A"
}}

The "answer" must be one of "A", "B", "C", or "D" — whichever option is correct."""

    # Retry up to 3 times — the API sometimes returns truncated JSON
    last_error = None
    for attempt in range(1, 4):
        raw_text = call_claude(prompt)

        # Sometimes Claude wraps JSON in markdown code blocks — strip those
        raw_text = raw_text.strip()
        if raw_text.startswith("```"):
            # Remove ```json (or just ```) from the beginning
            first_newline = raw_text.find("\n")
            if first_newline != -1:
                raw_text = raw_text[first_newline + 1:]
            # Remove closing ``` from the end
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

        try:
            question_data = json.loads(raw_text)
            question_data["topic"] = topic
            return question_data
        except json.JSONDecodeError as e:
            last_error = f"JSON parse error (attempt {attempt}): {e}"
            import time
            time.sleep(1)

    raise RuntimeError(f"Failed to generate valid question after 3 attempts: {last_error}")


if __name__ == "__main__":
    topic_to_test = "lists"
    print(f"Generating a question about: {topic_to_test}...\n")

    new_question = generate_question(topic_to_test)

    print("Generated question:")
    print(json.dumps(new_question, indent=2))
