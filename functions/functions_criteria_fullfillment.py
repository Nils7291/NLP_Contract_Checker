import time
import re
from openai import OpenAI
import json
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from key import OpenAiKey

print("Current working directory:", os.getcwd())
from key import OpenAiKey

client = OpenAI(api_key=OpenAiKey)


def check_core_aspects_with_llm(section_text, core_aspects, client, model="gpt-4o-mini", sleep_between_calls=1.5):
    """
    Uses an LLM to evaluate a section of a contract based on given core aspects.

    Parameters:
    - section_text: The section of the contract to evaluate
    - core_aspects: List of core aspect criteria (strings)
    - client: OpenAI client instance
    - model: Model to use (default is "gpt-4o-mini")
    - sleep_between_calls: Delay after the API call to manage rate limits

    Returns:
    - JSON string response from the LLM or None if the call fails
    """
    aspects_list = "\n- " + "\n- ".join(core_aspects)
    prompt = f"""Du bist ein Vertragsexperte. Prüfe den folgenden Vertragstext auf die Einhaltung der folgenden Kernanforderungen (Core Aspects).
                Gib als Ergebnis für jeden einzelnen Punkt einen Erfüllungsgrad von 0 bis 1 an (0 = nicht erfüllt, 1 = voll erfüllt, 0.5 = teilweise erfüllt). Gib zusätzlich eine durchschnittliche Erfüllungsquote in Prozent für alle Core Aspects an.
                Vertragstext:
                {section_text}
                Core Aspects:{aspects_list}
                Antwortformat (nur JSON):
                    {{
                    "core_aspect_scores": {{
                        "Aspekt 1": 1,
                        "Aspekt 2": 0.5
                    }},
                    "average_fulfillment_percent": 76.5
            }}"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        print("API-Fehler:", e)
        return None
    finally:
        time.sleep(sleep_between_calls)


def evaluate_fullfillment_on_criteria(row, content_column="section_content", criteria_column="core_aspects", client=client, model="gpt-4o-mini"):
    """
    Evaluates the fulfillment of core criteria for a given contract section.

    Parameters:
    - row: A row from a DataFrame, expected to contain contract content and criteria
    - content_column: Column name containing the contract section text
    - criteria_column: Column name containing the core aspects as newline-separated text
    - client: OpenAI client instance
    - model: Model to use for evaluation

    Returns:
    - Dictionary with:
        - "core_aspect_scores": Dict of aspect: score (0–1)
        - "average_fulfillment_percent": Average as float, or None if parsing fails
    """
    section_text = row[content_column]
    aspects = [line.strip() for line in str(row[criteria_column]).split("\n") if line.strip()]
    raw_response = check_core_aspects_with_llm(section_text, aspects, client=client, model=model, sleep_between_calls=1.5)

    try:
        # Special case: response may contain ```json or other markdown blocks
        match = re.search(r"{.*}", raw_response, re.DOTALL)
        if match:
            cleaned_json = match.group(0)
            print("✅ LLM response:", cleaned_json)
            return json.loads(cleaned_json)
        else:
            raise ValueError("No JSON block found.")
    except Exception:
        print("❌ Parsing error. Full response was:", raw_response)
        return {"core_aspect_scores": {}, "average_fulfillment_percent": None}
