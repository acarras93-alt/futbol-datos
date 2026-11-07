"""Organizar los Excel por club y registrar los movimientos.

Por defecto muestra una vista previa.
Con --apply mueve los archivos y guarda un manifiesto.
"""

import argparse
import json
import re
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

DISCOVERY_RUN_ID = "20261106T195158813262Z"


def team_slug(team_name):
    """Convertir el nombre del club en un texto apto para rutas."""
    normalized = unicodedata.normalize("NFKD", team_name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_name).strip("-") or "team"


def build_team_excel_path(output_dir, team_id, team_name, run_id):
    """Aplicar la misma convención a exportaciones actuales y futuras."""
    slug = team_slug(team_name)
    return (
        output_dir
        / "teams"
        / f"{slug}_{team_id}"
        / f"squad_{slug}_{team_id}_{run_id}.xlsx"
    )


def build_plan(project_root):
    """Preparar los movimientos sin crear carpetas ni mover archivos."""
    raw_dir = project_root / "data" / "raw"
    league_path = raw_dir / f"league_501_{DISCOVERY_RUN_ID}.json"
    league = json.loads(league_path.read_text(encoding="utf-8"))["response"]["data"]
    season_id = league["currentseason"]["id"]
    teams_path = raw_dir / f"teams_season_{season_id}_{DISCOVERY_RUN_ID}.json"
    teams = json.loads(teams_path.read_text(encoding="utf-8"))["response"]["data"]
    team_names = {str(team["id"]): team["name"] for team in teams}

    output_dir = project_root / "outputs"
    pattern = re.compile(r"squad_team_(\d+)_(\d{8}T\d{12}Z)\.xlsx")
    plan = []

    for source in sorted(output_dir.glob("squad_team_*.xlsx")):
        match = pattern.fullmatch(source.name)
        if not match:
            continue

        team_id, run_id = match.groups()
        if team_id not in team_names:
            raise ValueError(f"Unknown team ID in file: {source.name}")

        destination = build_team_excel_path(
            output_dir, team_id, team_names[team_id], run_id
        )
        if destination.exists():
            raise FileExistsError(f"Destination already exists: {destination}")
        plan.append((source, destination))

    destinations = [destination for _, destination in plan]
    if len(destinations) != len(set(destinations)):
        raise ValueError("Multiple files would have the same destination.")

    return plan


def main():
    parser = argparse.ArgumentParser(description="Organize existing team Excel files.")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    plan = build_plan(project_root)

    for source, destination in plan:
        print(source.relative_to(project_root))
        print("  ->", destination.relative_to(project_root))
    print("Files planned:", len(plan))

    if not args.apply or not plan:
        print("Preview only. Use --apply to move the planned files.")
        return

    # Registrar las rutas originales antes de ejecutar los movimientos.
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    manifest_path = project_root / "outputs" / f"organization_{run_id}.json"
    manifest = [
        {
            "source": source.relative_to(project_root).as_posix(),
            "destination": destination.relative_to(project_root).as_posix(),
        }
        for source, destination in plan
    ]
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    for source, destination in plan:
        destination.parent.mkdir(parents=True, exist_ok=True)
        source.rename(destination)

    print("Files moved:", len(plan))
    print("Manifest saved:", manifest_path)


if __name__ == "__main__":
    main()
