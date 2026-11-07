"""Consultar y exportar las plantillas actuales de una liga.

Descubre la temporada y sus clubes, reutiliza las funciones por equipo
y guarda un JSON y un Excel de cada plantilla.
"""

from pathlib import Path

from discover_league import discover_league
from export_squad import (
    export_to_excel,
    get_squad,
    load_api_token,
    save_snapshot,
    squad_to_dataframe,
)

project_root = Path(__file__).resolve().parents[1]


def main():
    # Cargar el token una sola vez.
    api_token = load_api_token(project_root)

    # Obtener los cludes de la temporada actual
    league, season, teams = discover_league(501, api_token)

    print("Competittion:", league["name"])
    print("Season:", season["name"])

    # Extraer las plantillas de la liga
    for team in teams:
        team_id = team["id"]
        team_name = team["name"]

        print("Processing team:", team_name)

        # Consultar la plantilla y conservar la respuesta.
        payload, source, retrieved_at = get_squad(
            team_id,
            api_token,
        )

        run_id = retrieved_at.strftime("%Y%m%dT%H%M%S%fZ")
        file_stem = f"squad_team_{team_id}_{run_id}"

        raw_path = project_root / "data" / "raw" / f"{file_stem}.json"
        save_snapshot(payload, source, retrieved_at, raw_path)

        # Transformar, comprobar y exportar este equipo.
        team_df = squad_to_dataframe(payload["data"])

        excel_path = project_root / "outputs" / f"{file_stem}.xlsx"
        export_to_excel(team_df, excel_path)

        print("Rows exported:", len(team_df))
        print("Missing values by column:")
        print(team_df.isna().sum())
        print("JSON saved:", raw_path)
        print("Excel saved:", excel_path)


if __name__ == "__main__":
    main()
