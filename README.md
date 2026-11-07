# Análisis de plantillas de fútbol con Python

Proyecto de aprendizaje para consultar, preparar y exportar plantillas actuales
mediante la API v3 de Sportmonks. Parte de una consulta del Celtic y amplía el
proceso a los clubes de la Scottish Premiership: conserva los JSON originales,
genera Excel individuales y consolida los registros para analizar vencimientos
de contratos.

El caso de uso nace de una necesidad del sector de representación: localizar
jugadores por club, posición y fecha de finalización de contrato. El alcance de
esta fase se limita a una competición y a los datos accesibles con la cuenta
utilizada.

## Resultados comprobados

La descarga del **6 de noviembre de 2026** identificó la competición `501`
(`Premiership`) y su temporada `28275` (`2026/2027`). El identificador de
temporada se obtuvo de la respuesta de la API; no se fija en las consultas de
descubrimiento.

| Comprobación                                                        | Resultado |
| ------------------------------------------------------------------- | --------: |
| Clubes recibidos y procesados                                       |        12 |
| Registros de plantilla consolidados                                 |       325 |
| Contratos que vencen entre 2026-11-06 y 2027-11-06, ambos incluidos |       129 |
| Contratos con fecha posterior al intervalo                          |       178 |
| Contratos con fecha desconocida                                     |        18 |
| Contratos ya vencidos en la fecha de consulta                       |         0 |
| Dorsales ausentes                                                   |         3 |
| Fechas de nacimiento ausentes                                       |         1 |

En esa descarga no faltaban identificadores, nombres, posiciones ni
nacionalidades. Los controles tampoco detectaron identificadores de jugador
duplicados dentro de un mismo club.

Estos son resultados de una instantánea del proveedor. No acreditan que las
fechas contractuales hayan sido contrastadas con anuncios oficiales ni que los
recuentos se mantengan en futuras consultas. Una plantilla actual tampoco
representa el historial completo de jugadores de una temporada.

## Datos y procedencia

Una fila representa un registro de plantilla recibido en una consulta concreta.
Los identificadores son de Sportmonks y se conservan como texto.

| Campo           | Procedencia                     | Significado                                     |
| --------------- | ------------------------------- | ----------------------------------------------- |
| `Player ID`     | `entry.player_id`               | Identificador del jugador.                      |
| `Name`          | `entry.player.name`             | Nombre informado por el proveedor.              |
| `Shirt number`  | `entry.jersey_number`           | Dorsal registrado.                              |
| `Contract end`  | `entry.end`                     | Fecha de finalización según el proveedor.       |
| `Position`      | `entry.position.name`           | Posición general en la plantilla.               |
| `Nationality`   | `entry.player.nationality.name` | Nacionalidad según la definición del proveedor. |
| `Date of birth` | `entry.player.date_of_birth`    | Fecha de nacimiento informada.                  |

Sportmonks describe `nationality_id` como la selección nacional que el jugador
ha elegido representar. El campo no acredita todas sus nacionalidades legales
ni equivale al país de nacimiento.

La consolidación añade `Team ID`, `Team name`, `League ID`, `League name`,
`Season ID`, `Season name` y `Retrieved at UTC`. La fecha UTC procede de cada
consulta de plantilla; no se sustituye por el momento de generar el Excel.

## Flujo y responsabilidades

| Script                      | Responsabilidad                                              | ¿Consulta la API?             |
| --------------------------- | ------------------------------------------------------------ | ----------------------------- |
| `src/discover_league.py`    | Descubrir temporada y clubes; guardar ambas respuestas.      | Sí                            |
| `src/export_squad.py`       | Exportar un equipo y proporcionar funciones reutilizables.   | Sí, al ejecutarlo como script |
| `src/export_league.py`      | Descubrir los clubes y recorrer sus plantillas.              | Sí                            |
| `src/consolidate_league.py` | Leer una descarga local, consolidar y analizar contratos.    | No                            |
| `src/organize_exports.py`   | Previsualizar o aplicar la organización de Excel existentes. | No                            |

Las funciones reutilizadas incluyen `load_api_token()`, `get_squad()`,
`save_snapshot()`, `squad_to_dataframe()` y `export_to_excel()`.
`discover_league()` devuelve la competición, la temporada y la lista de clubes.
Los cinco scripts operativos utilizan `main()` y la condición
`if __name__ == "__main__"`: importarlos permite reutilizar funciones sin iniciar
peticiones o exportaciones.

Las consultas siguen estos patrones:

```text
GET https://api.sportmonks.com/v3/football/leagues/501?include=currentSeason
GET https://api.sportmonks.com/v3/football/teams/seasons/{season_id}
GET https://api.sportmonks.com/v3/football/squads/teams/{team_id}?include=player.nationality;position
```

La relación de temporada recibida se llama `currentseason`, aunque el parámetro
de inclusión se escribe `currentSeason`. La autenticación utiliza la cabecera
`Authorization`; el token no se incorpora a las URL guardadas.

## Estructura del proyecto

```text
futbol-datos/
├── src/
│   ├── discover_league.py
│   ├── export_squad.py
│   ├── export_league.py
│   ├── consolidate_league.py
│   ├── organize_exports.py
│   └── examples/
│       ├── first_test.py
│       ├── first_request.py
│       ├── find_team.py
│       └── get_squad.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

Los ejemplos conservan las primeras prácticas con diccionarios y consultas del
Celtic. No forman parte del flujo operativo. Los tres que consultan la API
mantienen `Path(__file__).resolve().parents[1]`: desde `src/examples/` esa ruta
apunta a `src/`. Antes de reutilizarlos hay que ajustar la raíz a `parents[2]`,
o mover `examples/` junto a `src/`, para cargar el `.env` de la raíz del proyecto.

Las carpetas locales siguientes están excluidas de Git:

- `data/raw/`: respuestas originales y contexto de consulta.
- `outputs/`: Excel y manifiestos de organización.
- `.venv/`, `source/` y cachés: entornos y archivos auxiliares.

`data/processed/` no se utiliza en el flujo actual.

## Preparación del entorno

Requisitos: Python 3.12 y una cuenta de Sportmonks con acceso a la competición.
Las dependencias están fijadas en `requirements.txt`.

En una instalación nueva, desde la raíz del repositorio:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Si el entorno ya existe, reutilizarlo con `source .venv/bin/activate`.
Configurar el token propio localmente en `.env`:

```dotenv
SPORTMONKS_API_TOKEN=YOUR_TOKEN
```

El repositorio no incluye credenciales, descargas JSON ni Excel. Una copia
nueva del código necesita obtener sus propios datos antes de consolidarlos.

## Ejecución

Ejecutar los comandos desde la raíz del proyecto con el entorno activo.

### Descubrir la temporada y los clubes

```bash
python src/discover_league.py
```

Guarda `league_501_{run_id}.json` y
`teams_season_{season_id}_{run_id}.json` en `data/raw/`. Ambos comparten un
identificador de ejecución, pero cada respuesta conserva su propio momento UTC.

### Consultar y exportar plantillas

Para la liga completa:

```bash
python src/export_league.py
```

Este comando ya incluye el descubrimiento; no requiere ejecutar el anterior
primero. Después realiza una petición por club. Para los 12 clubes de la
descarga comprobada fueron 14 peticiones en total.

Para un equipo individual:

```bash
python src/export_squad.py
```

Su configuración inicial es `TEAM_ID = 53` y `TEAM_NAME = "Celtic"`.
`TEAM_ID` determina la consulta; `TEAM_NAME` es una etiqueta descriptiva y no
valida la correspondencia del equipo.

Los dos exportadores guardan los archivos con este patrón:

```text
data/raw/squad_team_{team_id}_{run_id}.json
outputs/squad_team_{team_id}_{run_id}.xlsx
```

Cada pareja comparte una marca UTC. Las consultas nuevas generan archivos
nuevos. Los Excel son instantáneas y no se actualizan automáticamente.

### Consolidar y analizar sin nuevas peticiones

```bash
python src/consolidate_league.py
```

La selección de archivos está delimitada por estas constantes, correspondientes
a la descarga comprobada:

```python
DISCOVERY_RUN_ID = "20261106T195158813262Z"
LAST_SQUAD_RUN_ID = "20261106T195202812344Z"
```

La primera identifica los JSON de competición y clubes, y el límite inferior
de selección de plantillas. La segunda marca el último JSON de plantilla de
esa ejecución. Se exige exactamente un archivo por club dentro del intervalo.
Los nombres usan un formato UTC fijo, cuyo orden alfabético coincide con el
temporal. Así se evita elegir simplemente la última consulta de cada club y
mezclar descargas diferentes.

Para otra descarga hay que actualizar las constantes en el consolidador y, si
se utiliza, `DISCOVERY_RUN_ID` en el organizador. Ejecutar el exportador no
actualiza esas selecciones automáticamente.

El Excel conjunto se genera en:

```text
outputs/league_{league_id}_season_{season_id}_{DISCOVERY_RUN_ID}.xlsx
```

| Hoja                 | Contenido de la descarga comprobada                                |
| -------------------- | ------------------------------------------------------------------ |
| `Squad`              | 325 registros, siete campos originales y siete de contexto.        |
| `Expiring 12 months` | 129 registros, ordenados por fecha de contrato ascendente.         |
| `Coverage`           | 12 clubes, con filas y ausencias de contrato, dorsal y nacimiento. |

`Squad` conserva el orden de clubes de la respuesta y el orden descendente de
contratos dentro de cada plantilla, con fechas ausentes al final. La cobertura
completa se contrasta con los clubes del JSON de temporada; no implica verificar
independientemente toda la plantilla real de cada club.

Volver a consolidar la misma descarga reconstruye y sobrescribe su Excel
conjunto. Los JSON originales se conservan.

### Organizar las exportaciones individuales

Primero mostrar el plan:

```bash
python src/organize_exports.py
```

Para aplicar los movimientos revisados:

```bash
python src/organize_exports.py --apply
```

El organizador reconoce los Excel de la raíz de `outputs/` con el patrón
`squad_team_ID_UTC.xlsx`. Recupera los nombres de club del JSON local y los
coloca en:

```text
outputs/teams/{club}_{team_id}/squad_{club}_{team_id}_{run_id}.xlsx
```

Conserva el contenido, ID y marca UTC; detecta destinos ocupados y registra las
rutas originales y nuevas en `outputs/organization_{run_id}.json` antes de
mover los archivos. No convierte formatos ni organiza nombres antiguos que no
coincidan con el patrón.

La organización local utilizada también reserva `outputs/league/` para el Excel
conjunto y `outputs/manifests/` para el manifiesto. En esta versión esos dos
archivos se generan todavía en la raíz de `outputs/` y pueden moverse allí
manualmente. Las siguientes ejecuciones vuelven a escribir en las rutas
configuradas en el código. Los JSON de `data/raw/` mantienen sus nombres porque
se utilizan para consolidar.

## Criterio de vencimientos y controles

El intervalo utiliza la **fecha UTC de consulta de cada plantilla**, normalizada
al día, y suma **doce meses naturales** con `pd.DateOffset(months=12)`.
Se incluyen ambos extremos:

```text
fecha de consulta <= Contract end <= fecha de consulta + 12 meses
```

Los contratos sin fecha son desconocidos y se contabilizan por separado.
Los ya vencidos quedan fuera del filtro futuro. El cálculo permanece ligado
a la consulta original: consolidar otro día no cambia el intervalo de esos datos.

Controles implementados:

- Tiempo de espera y comprobación de errores HTTP.
- Comprobación de competición y pertenencia de la temporada descubierta.
- Lista de clubes y plantillas no vacías.
- Identificadores de jugador no nulos y sin duplicados dentro del club.
- Conversión de dorsales a enteros anulables y de contratos y nacimientos a fechas.
- Unicidad del par `Team ID` y `Player ID` al consolidar.
- Recuento de ausencias y conservación de la respuesta original con origen y UTC.
- Filtros, cabeceras inmovilizadas, fechas `yyyy-mm-dd` y `Player ID` oculto
  en las hojas de jugadores.

Los scripts se detienen ante errores; no incluyen todavía reintentos ni un
registro acumulado de clubes fallidos para continuar la descarga. `Coverage`
resume una consolidación completada, no un historial de fallos. La ausencia de
metadatos de paginación observada en la respuesta de clubes no se interpreta
como `has_more=False`: para esta ejecución se contrastó el listado de 12 clubes.

## Validación y límites de los datos

En la prueba inicial del Celtic del 5 de noviembre de 2026 se obtuvieron 29
registros sin ausencias en los siete campos. Se contrastaron visualmente nombres
y dorsales con la [plantilla oficial del Celtic](https://www.celticfc.com/teams/).
Esa revisión no se extiende a todos los clubes ni a todos los campos.

Las fechas de nacimiento y de contrato no se han contrastado de forma
independiente. Los contratos pueden estar desactualizados y requieren evidencia
específica, como anuncios oficiales de fichajes o renovaciones. Los ajustes
manuales guardados en Numbers no forman parte de la exportación de Python.

La cobertura depende de la suscripción. No se han confirmado una fuente
autorizada ni soporte suficiente para representantes y valoraciones de mercado.
Esta fase no incluye otras ligas, una base de datos, una aplicación, un dashboard
ni actualización programada.

Se publica código y documentación. Las credenciales y los datos descargados se
conservan localmente y están excluidos de Git; compartir los datos requiere
comprobar las condiciones del proveedor.

## Recorrido de aprendizaje

El desarrollo se realizó con apoyo de documentación y asistencia de IA,
especialmente durante la refactorización y organización. Las comprobaciones
del resultado permiten distinguir comportamiento demostrado de datos pendientes
de contraste.

1. Pasar de diccionarios y consultas básicas a una exportación de un club.
1. Separar consulta, guardado, transformación y Excel en funciones reutilizables.
1. Recorrer los clubes y comprobar que la consulta y exportación están dentro del bucle.
1. Consolidar los JSON guardados con `pd.concat()` y conservar el contexto.
1. Analizar fechas conocidas y ausentes, y organizar los resultados con trazabilidad.

Durante el proceso se corrigieron la extracción del nombre desde `player`,
errores de sangría que procesaban únicamente el último registro o club, y el
formato de fechas al añadir hojas al Excel.

## Revisión del código

```bash
python -m ruff check src
python -m ruff format --check src
```

Estas revisiones no consultan la API. Comprueban código y formato, pero no
demuestran por sí solas el comportamiento del flujo ni la veracidad deportiva.
Los recuentos anteriores se comprobaron sobre los JSON guardados y el Excel.

## Documentación

- [Competición por ID](https://docs.sportmonks.com/v3/endpoints-and-entities/endpoints/leagues/get-league-by-id)
- [Clubes por temporada](https://docs.sportmonks.com/v3/endpoints-and-entities/endpoints/teams/get-teams-by-season-id)
- [Plantilla por equipo](https://docs.sportmonks.com/v3/endpoints-and-entities/endpoints/team-squads/get-team-squad-by-team-id)
- [Datos y relaciones de un jugador](https://docs.sportmonks.com/v3/endpoints-and-entities/endpoints/players/get-player-by-id)
- [Autenticación](https://docs.sportmonks.com/v3/welcome/authentication)
- [pandas: exportación a Excel](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_excel.html)
- [openpyxl: tablas](https://openpyxl.readthedocs.io/en/stable/worksheet_tables.html)
