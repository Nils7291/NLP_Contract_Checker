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