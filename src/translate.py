import pandas as pd
import requests
import os

DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")  # Stelle sicher, dass dein Key als Umgebungsvariable gesetzt ist

def translate_text(text, target_lang="DE"):
    if not text or not isinstance(text, str):
        return text

    params = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "source_lang": "EN",
        "target_lang": target_lang
    }

    try:
        response = requests.post(DEEPL_API_URL, data=params)
        response.raise_for_status()
        result = response.json()
        return result["translations"][0]["text"]
    except requests.exceptions.HTTPError as e:
        print(f"⚠️ Fehler bei Text: {text[:40]}... → {e}")
        return text  # Gib den Originaltext zurück, wenn es schiefgeht


import time

def translate_dataframe(df, text_column="Content", lang_column="Sprache", target_lang="DE"):
    df = df.copy()
    mask = df[lang_column] == "EN"

    for idx in df[mask].index:
        original_text = df.at[idx, text_column]
        try:
            translated = translate_text(original_text, target_lang)
            df.at[idx, text_column] = translated
        except Exception as e:
            print(f"⚠️ Fehler bei Zeile {idx}: {e}")
            # Optional: warte kurz, falls Rate-Limit
            time.sleep(1)

    return df

