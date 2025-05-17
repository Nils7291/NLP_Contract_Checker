# NLP_Contract_Checker

Bei erster installation oder nuestart:
1. Virtuelle Umgebung aktivieren:
Virtuelle Umgebung erstellen:
uv venv .venv --python=python3.11
Windows (PowerShell):
.venv\Scripts\Activate.ps1
macOS/Linux:
source .venv/bin/activate



2. Abhängigkeiten installieren:
uv pip sync requirements.txt

Neue Python-Pakete installieren und zur requirements.txt hinzufügen:
    - Neue Pakete in requirements.in schreiben
    - im Terminal: 
        uv pip compile requirements.in > requirements.txt
    - umgebung syncronisieren: 
        uv pip sync requirements.txt

## Cleaning
- Aktuell: def clean_paragraph_text(text):
    - 1. remove paragraph marker z. B. '§ 1' oder '1.'
    - 2. remove punctation
    - 3. remove double whitespaces
    - 4. remove whitespace beginning and end
    
## Models:
- Aktuelle models: BERT, SBERT, GBERT, JInai
"jinaai/jina-embeddings-v3"
"bert-base-cased"
"deepset/gbert-base"