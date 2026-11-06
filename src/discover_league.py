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

url = "https://api.sportmonks.com/v3/football/leagues/501"

headers = {
    "Authorization": api_token,
    "Accept": "application/json",
}

# Consultar la competición e incluir su temporada actual.
response = requests.get(
    url,
    params={"include": "currentSeason"},
    headers=headers,
    timeout=20,
)

print("HTTP status:", response.status_code)
response.raise_for_status()

payload = response.json()


# La respuesta contiene una sola competición.
league = payload["data"]

print("League ID:", league["id"])
print("League name:", league["name"])

# Inspeccionar los campos antes de extraer la temporada.
print("League fields:", list(league.keys()))


# Extraer la temporada actual incluida en la respuesta.
season = league.get("currentseason")

if not season:
    raise SystemExit("Current season not found.")

# Mostrar los datos necesarios para comprobar la temporada.
print("Season ID:", season.get("id"))
print("Season name:", season.get("name"))
print("Season league ID:", season.get("league_id"))
print("Is current:", season.get("is_current"))
print("Finished:", season.get("finished"))
print("Pending:", season.get("pending"))
print("Starting at:", season.get("starting_at"))
print("Ending at:", season.get("ending_at"))
