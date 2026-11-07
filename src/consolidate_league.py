"""Consolidar y analizar las plantillas de una descarga guardada.

Lee los JSON locales y añade el contexto de club, competición y temporada.
Genera un Excel con las plantillas, los vencimientos a doce meses y la cobertura.
"""

import json
from pathlib import Path

import pandas as pd

from export_squad import export_to_excel, squad_to_dataframe

project_root = Path(__file__).resolve().parents[1]

# Delimitar la descarga comprobada, sin incorporar otras consultas.
DISCOVERY_RUN_ID = "20261106T195158813262Z"
LAST_SQUAD_RUN_ID = "20261106T195202812344Z"


def load_snapshot(path):
    """Leer un JSON guardado, sin consultar la API."""
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    raw_dir = project_root / "data" / "raw"

    league_path = raw_dir / f"league_501_{DISCOVERY_RUN_ID}.json"
    league = load_snapshot(league_path)["response"]["data"]
    season = league["currentseason"]

    teams_path = raw_dir / f"teams_season_{season['id']}_{DISCOVERY_RUN_ID}.json"
    teams = load_snapshot(teams_path)["response"]["data"]

    team_frames = []
    coverage = []

    for team in teams:
        # Exigir un único archivo de este club dentro de la descarga elegida.
        candidates = [
            path
            for path in raw_dir.glob(f"squad_team_{team['id']}_*.json")
            if DISCOVERY_RUN_ID <= path.stem.rsplit("_", 1)[1] <= LAST_SQUAD_RUN_ID
        ]

        if len(candidates) != 1:
            raise ValueError(
                f"Expected one snapshot for {team['name']}; found {len(candidates)}."
            )

        snapshot = load_snapshot(candidates[0])
        team_df = squad_to_dataframe(snapshot["response"]["data"])

        coverage.append(
            {
                "Team ID": str(team["id"]),
                "Team name": team["name"],
                "Rows": len(team_df),
                "Missing Contract end": int(team_df["Contract end"].isna().sum()),
                "Missing Shirt number": int(team_df["Shirt number"].isna().sum()),
                "Missing Date of birth": int(team_df["Date of birth"].isna().sum()),
            }
        )

        # Añadir el contexto sin alterar las siete columnas originales.
        team_df["Team ID"] = str(team["id"])
        team_df["Team name"] = team["name"]
        team_df["League ID"] = str(league["id"])
        team_df["League name"] = league["name"]
        team_df["Season ID"] = str(season["id"])
        team_df["Season name"] = season["name"]
        team_df["Retrieved at UTC"] = snapshot["retrieved_at_utc"]

        team_frames.append(team_df)

    # Reunir las tablas conservando una fila por registro de plantilla.
    league_df = pd.concat(team_frames, ignore_index=True)
    coverage_df = pd.DataFrame(coverage)

    if league_df.duplicated(["Team ID", "Player ID"]).any():
        raise ValueError("Duplicate player IDs within a team.")

    # Obtener la fecha UTC de consulta de cada registro.
    query_dates = (
        pd.to_datetime(league_df["Retrieved at UTC"], utc=True)
        .dt.tz_localize(None)
        .dt.normalize()
    )

    # Calcular doce meses naturales desde la consulta.
    window_end = query_dates + pd.DateOffset(months=12)
    contract_dates = league_df["Contract end"]

    # Seleccionar contratos conocidos dentro del intervalo futuro.
    expiring_df = league_df.loc[
        contract_dates.notna()
        & contract_dates.ge(query_dates)
        & contract_dates.le(window_end)
    ].copy()

    expiring_df = expiring_df.sort_values("Contract end")

    print("Contracts expiring within 12 months:", len(expiring_df))
    print("Unknown contract dates:", contract_dates.isna().sum())
    print("Already expired:", contract_dates.lt(query_dates).sum())

    excel_path = (
        project_root
        / "outputs"
        / f"league_{league['id']}_season_{season['id']}_{DISCOVERY_RUN_ID}.xlsx"
    )
    export_to_excel(league_df, excel_path)

    # Añadir el análisis y la cobertura al Excel conjunto.
    with pd.ExcelWriter(
        excel_path,
        engine="openpyxl",
        mode="a",
        if_sheet_exists="replace",
        datetime_format="yyyy-mm-dd",
    ) as writer:
        expiring_df.to_excel(
            writer,
            sheet_name="Expiring 12 months",
            index=False,
            freeze_panes=(1, 0),
        )

        coverage_df.to_excel(
            writer,
            sheet_name="Coverage",
            index=False,
            freeze_panes=(1, 0),
        )

        # Mantener oculto el identificador del jugador.
        writer.sheets["Expiring 12 months"].column_dimensions["A"].hidden = True

        # Activar filtros en las nuevas hojas.
        for sheet_name in ("Expiring 12 months", "Coverage"):
            worksheet = writer.sheets[sheet_name]
            worksheet.auto_filter.ref = worksheet.dimensions

        # Ajustar los anchos sin reducir los ya configurados.
        widths = {
            "Name": 42,
            "Team name": 24,
            "Nationality": 24,
            "Retrieved at UTC": 36,
        }

        for worksheet in writer.book.worksheets:
            for header in worksheet[1]:
                column = header.column_letter
                width = widths.get(
                    header.value,
                    max(18, len(str(header.value)) + 2),
                )

                current_width = worksheet.column_dimensions[column].width
                worksheet.column_dimensions[column].width = max(
                    current_width or 0,
                    width,
                )

                # Aplicar fechas sin hora en las hojas de jugadores.
                if header.value in ("Contract end", "Date of birth"):
                    for cell in worksheet[column][1:]:
                        cell.number_format = "yyyy-mm-dd"

    print(coverage_df.to_string(index=False))
    print("Teams consolidated:", league_df["Team ID"].nunique())
    print("Rows consolidated:", len(league_df))
    print("Missing values by column:")
    print(league_df.isna().sum())
    print("Excel saved:", excel_path)


if __name__ == "__main__":
    main()
