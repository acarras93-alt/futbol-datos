"""Descubrir la temporada actual y los clubes de una competición.

Consulta Sportmonks y conserva ambas respuestas JSON con contexto UTC.
Devuelve la competición, la temporada y la lista de clubes.
"""

from datetime import UTC, datetime
from pathlib import Path

import requests

from export_squad import load_api_token, save_snapshot

project_root = Path(__file__).resolve().parents[1]


def discover_league(league_id, api_token):
    """Obtener la competición, su temporada actual y sus clubes."""
    url = f"https://api.sportmonks.com/v3/football/leagues/{league_id}"
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
    retrieved_at = datetime.now(UTC)
    run_id = retrieved_at.strftime("%Y%m%dT%H%M%S%fZ")

    # Conservar la respuesta original antes de comprobar sus datos.
    raw_dir = project_root / "data" / "raw"
    raw_path = raw_dir / f"league_{league_id}_{run_id}.json"
    save_snapshot(payload, response.url, retrieved_at, raw_path)

    league = payload["data"]
    if league.get("id") != league_id:
        raise ValueError("Unexpected league ID. Review the source response.")

    print("League ID:", league["id"])
    print("League name:", league["name"])

    # La relación recibida se llama currentseason, en minúsculas.
    season = league.get("currentseason")
    if not season or not season.get("id"):
        raise ValueError("Current season not found.")
    if season.get("league_id") != league_id:
        raise ValueError("Current season does not belong to the requested league.")

    print("Season ID:", season["id"])
    print("Season name:", season.get("name"))
    print("Season league ID:", season["league_id"])
    print("Is current:", season.get("is_current"))
    print("Finished:", season.get("finished"))
    print("Pending:", season.get("pending"))
    print("Starting at:", season.get("starting_at"))
    print("Ending at:", season.get("ending_at"))
    print("Retrieved at UTC:", retrieved_at.isoformat())
    print("League JSON saved:", raw_path)

    # Utilizar el identificador descubierto para consultar sus clubes.
    season_id = season["id"]
    teams_url = f"https://api.sportmonks.com/v3/football/teams/seasons/{season_id}"
    print("Teams URL:", teams_url)

    teams_response = requests.get(teams_url, headers=headers, timeout=20)
    print("Teams HTTP status:", teams_response.status_code)
    teams_response.raise_for_status()

    teams_payload = teams_response.json()
    teams_retrieved_at = datetime.now(UTC)

    # Agrupar ambas respuestas con el mismo identificador de ejecución.
    teams_raw_path = raw_dir / f"teams_season_{season_id}_{run_id}.json"
    save_snapshot(
        teams_payload,
        teams_response.url,
        teams_retrieved_at,
        teams_raw_path,
    )

    teams = teams_payload["data"]
    if not isinstance(teams, list) or not teams:
        raise ValueError("No team list received. Review the source response.")

    print("Teams received:", len(teams))
    for team in teams:
        print(team["id"], "-", team["name"])
    print("Teams JSON saved:", teams_raw_path)

    # Devolver los datos para que otro script pueda reutilizarlos.
    return league, season, teams


def main():
    """Ejecutar el descubrimiento desde la terminal."""
    api_token = load_api_token(project_root)
    discover_league(501, api_token)


if __name__ == "__main__":
    main()
