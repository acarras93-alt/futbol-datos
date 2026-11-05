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

url = "https://api.sportmonks.com/v3/football/squads/teams/53?include=player"

headers = {
    "Authorization": api_token,
    "Accept": "application/json",
}

response = requests.get(url, headers=headers, timeout=20)

print("HTTP status:", response.status_code)
response.raise_for_status()

payload = response.json()

squad = payload["data"]

print("Squad records:", len(squad))
print("Player ID | Name | Shirt number | Contract end")

for entry in squad:
    player = entry.get("player") or {}

    print(
        entry.get("player_id"),
        "|",
        player.get("name", "Name unavailable"),
        "|",
        entry.get("jersey_number"),
        "|",
        entry.get("end"),
    )
