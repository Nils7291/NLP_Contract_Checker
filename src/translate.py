import os
import requests
from dotenv import load_dotenv
import pandas as pd

# .env-Datei laden
load_dotenv()

# API-Key aus Umgebungsvariable
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")

if not DEEPL_API_KEY:
    raise ValueError("❌ Kein DEEPL_API_KEY gefunden. Bitte .env-Datei anlegen oder Umgebungsvariable setzen.")

def translate_deepl(text, source_lang="EN", target_lang="DE"):
    """
    Übersetzt einen Text von Englisch nach Deutsch mit der DeepL API.
    """
    url = "https://api-free.deepl.com/v2/translate"
    
    headers = {
        "Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"
    }

    data = {
        "text": text,
        "source_lang": source_lang,
        "target_lang": target_lang
    }

    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()  # raises an exception if the response code was 4xx/5xx
    result = response.json()
    return result["translations"][0]["text"]

def translate_english_documents(df, text_column="Content", lang_column="Sprache"):
    """
    Übersetzt alle Zeilen im DataFrame, bei denen Sprache 'EN' ist.
    """
    for idx, row in df.iterrows():
        if str(row.get(lang_column)).strip().upper() == "EN":
            original = row.get(text_column)
            if pd.notna(original) and original.strip():
                try:
                    translated = translate_deepl(original)
                    df.at[idx, text_column] = translated
                    print(f"✅ Document {idx} erfolgreich übersetzt.")
                except Exception as e:
                    print(f"⚠️ Fehler bei Zeile {idx}: {e}")
    return df
