import json
import os
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.table import Table, TableStyleInfo

# 1. Configuración del equipo que queremos consultar.
TEAM_ID = 53
TEAM_NAME = "Celtic"

project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / ".env")

api_token = os.getenv("SPORTMONKS_API_TOKEN")

if not api_token:
    raise SystemExit("Missing API token. Check yout .env file.")

print("Token loaded locally.")

# URL de consulta
url = (
    f"https://api.sportmonks.com/v3/football/"
    f"squads/teams/{TEAM_ID}?include=player.nationality;position"
)

headers = {
    "Authorization": api_token,
    "Accept": "application/json",
}

response = requests.get(url, headers=headers, timeout=20)

print("HTTP status:", response.status_code)
response.raise_for_status()

payload = response.json()

# 2. Guarda la respuesta y el contexto de la consulta.
retrieved_at = datetime.now(UTC)
run_id = retrieved_at.strftime("%Y%m%dT%H%M%S%fZ")

raw_dir = project_root / "data" / "raw"
raw_dir.mkdir(parents=True, exist_ok=True)

snapshot = {
    "source": url,
    "retrieved_at_utc": retrieved_at.isoformat(),
    "response": payload,
}

raw_path = raw_dir / f"squad_team_{TEAM_ID}_{run_id}.json"
raw_path.write_text(
    json.dumps(snapshot, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

# 3. Construir una fila por registro de plantilla.
squad = payload["data"]

rows = []

for entry in squad:
    player = entry.get("player") or {}
    position = entry.get("position") or {}
    nationality = player.get("nationality") or {}

    rows.append(
        {
            "Player ID": entry.get("player_id"),
            "Name": player.get("name"),
            "Shirt number": entry.get("jersey_number"),
            "Contract end": entry.get("end"),
            "Position": position.get("name"),
            "Nationality": nationality.get("name"),
            "Date of birth": player.get("date_of_birth"),
        }
    )

df = pd.DataFrame(rows)

# 4. Comprobar identificadores y tipos de datos.
if df.empty:
    raise SystemExit("No squad records received.")

if df["Player ID"].isna().any():
    raise SystemExit("Missing player IDs. Review the source response.")

# Duplicados: detenemos la exportación para revisarlos(investigar)
if df["Player ID"].duplicated().any():
    raise SystemExit("Duplicate player IDs. Review the source response.")

df["Player ID"] = df["Player ID"].astype("string")
df["Shirt number"] = df["Shirt number"].astype("Int64")
df["Contract end"] = pd.to_datetime(
    df["Contract end"], format="%Y-%m-%d", errors="raise"
)
# Convertir la fecha de nacimiento al tipo de dato adecuado.
df["Date of birth"] = pd.to_datetime(
    df["Date of birth"],
    format="%Y-%m-%d",
    errors="raise",
)

# Ordenar por finalización de contrato: las fechas más lejanas primero.
df = df.sort_values(
    by="Contract end",
    ascending=False,
    na_position="last",
)

# 5. Exportar la tabla
output_dir = project_root / "outputs"
output_dir.mkdir(parents=True, exist_ok=True)

excell_path = output_dir / f"squad_team_{TEAM_ID}_{run_id}.xlsx"

with pd.ExcelWriter(
    excell_path,
    engine="openpyxl",
    datetime_format="yyyy-mm-dd",
) as writer:
    df.to_excel(
        writer,
        sheet_name="Squad",
        index=False,
        freeze_panes=(1, 0),
    )

    worksheet = writer.sheets["Squad"]

    # Aplicar el formato de fecha a contratos y nacimientos.
    for column in ("D", "G"):
        for cell in worksheet[column][1:]:
            cell.number_format = "yyyy-mm-dd"

    worksheet.column_dimensions["A"].width = 16
    worksheet.column_dimensions["B"].width = 32
    worksheet.column_dimensions["C"].width = 18
    worksheet.column_dimensions["D"].width = 20

    # Crear una tabla de Excel que incluya los encabezados y todos los registros de jugadores
    table = Table(
        displayName="CelticSquad",
        ref=worksheet.dimensions,
    )

    worksheet.add_table(table)

    table.tableStyleInfo = TableStyleInfo(
        name="TableStyleLight1",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=False,
        showColumnStripes=False,
    )
    # Aplicar encabezados explicitos
    for cell in worksheet[1]:
        cell.font = Font(bold=True, color="FFFFFFFF")
        cell.fill = PatternFill(
            fill_type="solid",
            fgColor="FF17365D",
        )

    worksheet.row_dimensions[1].height = 24
    worksheet.column_dimensions["B"].width = 42

    # Alinear cada columna de forma coherente, incluido su encabezado.
    for row in worksheet.iter_rows():
        for cell in row:
            cell.alignment = Alignment(
                horizontal="left" if cell.column <= 2 else "center",
                vertical="center",
            )

            if cell.row > 1:
                cell.font = Font(name="Arial", size=11)

    # Dar más espacio a las filas para facilitar la lectura.
    for row_number in range(2, worksheet.max_row + 1):
        worksheet.row_dimensions[row_number].height = 22

    worksheet.row_dimensions[1].height = 28

    # Establecer los anchos de las columnas.
    worksheet.column_dimensions["A"].width = 14
    worksheet.column_dimensions["B"].width = 42
    worksheet.column_dimensions["C"].width = 18
    worksheet.column_dimensions["D"].width = 18
    worksheet.column_dimensions["E"].width = 22
    worksheet.column_dimensions["F"].width = 24
    worksheet.column_dimensions["G"].width = 18

    # Definir un borde fino y uniforme.
    thin_border = Side(style="thin", color="FFD9E1E8")

    # Delimitar todas las celdas y dejar el cuerpo de la tabla blanco.
    for row in worksheet.iter_rows():
        for cell in row:
            cell.border = Border(
                left=thin_border,
                right=thin_border,
                top=thin_border,
                bottom=thin_border,
            )

            if cell.row > 1:
                cell.fill = PatternFill(
                    fill_type="solid",
                    fgColor="FFFFFFFF",
                )

print("Rows exported:", len(df))
print("Missing values by column:")
print(df.isna().sum())
print("Excel saved:", excell_path)
