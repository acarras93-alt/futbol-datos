"""Buscar el Celtic en Sportmonks y mostrar las coincidencias recibidas.

Ejemplo de consulta por nombre utilizando un token cargado localmente.
"""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / ".env")

api_token = os.getenv("SPORTMONKS_API_TOKEN")

if not api_token:
    raise SystemExit("Missing API token. Check yout .env file.")

print("Token loaded locally.")

url = "https://api.sportmonks.com/v3/football/teams/search/Celtic"

headers = {
    "Authorization": api_token,
    "Accept": "application/json",
}

response = requests.get(url, headers=headers, timeout=20)

print("HTTP status:", response.status_code)
response.raise_for_status()

payload = response.json()

for team in payload["data"]:
    print(team["id"], "-", team["name"])
