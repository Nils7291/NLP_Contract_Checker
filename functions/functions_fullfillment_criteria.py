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
    section_text = row[content_column]  # section_text = row["clean_section_content"]
    aspects = [line.strip() for line in str(row[criteria_column]).split("\n") if line.strip()]
    raw_response = check_core_aspects_with_llm(section_text, aspects, client=client, model=model, sleep_between_calls=1.5)
    # Versuche, reines JSON aus der Antwort zu extrahieren
    try:
        # Sonderfall: Antwort enthält ```json ... ``` oder anderen Markdown-Block
        match = re.search(r"{.*}", raw_response, re.DOTALL)
        if match:
            cleaned_json = match.group(0)
            print("✅ LLM-Antwort:", cleaned_json)
            return json.loads(cleaned_json)
        else:
            raise ValueError("Kein JSON-Block gefunden.")
    except Exception:
        print("❌ Parsing-Fehler. Antwort war:", raw_response)
        return {"core_aspect_scores": {}, "average_fulfillment_percent": None}


