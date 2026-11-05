# Análisis de plantillas de fútbol con Python

Proyecto personal de consulta, preparación y exportación de datos de plantillas
profesionales mediante la API v3 de Sportmonks. El resultado es una tabla Excel
con filtros, fechas reconocidas como fechas y una presentación reproducible
desde Python.

El caso de uso parte de una necesidad del sector de representación: localizar
jugadores por características deportivas y vencimiento de contrato. Este
prototipo demuestra la obtención y organización de datos; todavía no cubre la
búsqueda de representantes ni la cobertura mundial.

## Alcance actual

La prueba utiliza el Celtic, con el identificador `53` de Sportmonks. El script
de exportación permite configurar otro equipo, siempre que sea accesible con la
suscripción utilizada y la respuesta conserve la estructura esperada.

Una fila representa un registro de plantilla recibido en una consulta concreta.
Los identificadores pertenecen a Sportmonks; no son los dorsales ni deben
equipararse directamente con identificadores de otros proveedores.

| Campo           | Procedencia                     | Significado                                                        |
| --------------- | ------------------------------- | ------------------------------------------------------------------ |
| `Player ID`     | `entry.player_id`               | Identificador del jugador en Sportmonks.                           |
| `Name`          | `entry.player.name`             | Nombre informado por el proveedor.                                 |
| `Shirt number`  | `entry.jersey_number`           | Dorsal registrado en la plantilla.                                 |
| `Contract end`  | `entry.end`                     | Finalización del contrato según el proveedor.                      |
| `Position`      | `entry.position.name`           | Posición general del jugador en la plantilla.                      |
| `Nationality`   | `entry.player.nationality.name` | País asociado a la nacionalidad según la definición de Sportmonks. |
| `Date of birth` | `entry.player.date_of_birth`    | Fecha de nacimiento informada por el proveedor.                    |

Sportmonks describe `nationality_id` como la selección nacional que el jugador
ha elegido representar. Este campo no acredita todas sus nacionalidades legales
ni debe confundirse con el país de nacimiento.

La tabla se ordena por finalización de contrato, desde las fechas más lejanas
hasta las más próximas; las fechas ausentes se colocan al final. Esto representa
tiempo contractual restante, no antigüedad en el club ni permanencia
garantizada.

## Fuente y acceso

Se utiliza una cuenta de Sportmonks y un token personal guardado localmente en
`.env`. En esta prueba, la cuenta permitió consultar las competiciones de
Dinamarca y Escocia incluidas en su acceso.

La consulta de exportación sigue este patrón:

```text
GET https://api.sportmonks.com/v3/football/squads/teams/{TEAM_ID}?include=player.nationality;position
```

La autenticación se realiza mediante la cabecera `Authorization`. El token no se
incorpora a la URL ni se publica en el repositorio.

## Proceso

1. Cargar la configuración y el token desde el entorno local.
1. Realizar la petición con un tiempo de espera y comprobar el estado HTTP.
1. Guardar el JSON recibido junto con la URL y la fecha de consulta en UTC.
1. Extraer los campos de plantilla y sus relaciones con jugador y posición.
1. Construir un DataFrame con pandas y comprobar identificadores y tipos.
1. Ordenar por finalización del contrato.
1. Generar un Excel mediante openpyxl e informar de valores ausentes.

Cada exportación realiza una nueva consulta. El Excel es una instantánea: no
mantiene una conexión activa ni se actualiza automáticamente después de crearse.

## Controles y presentación

- Detención ante respuestas HTTP de error y ausencia del token.
- Detención si la plantilla está vacía o contiene identificadores ausentes o
  duplicados.
- Identificadores conservados como texto y dorsales como enteros que admiten
  valores ausentes.
- Contratos y nacimientos convertidos a fechas con formato esperado; los valores
  ausentes pueden permanecer sin fecha.
- Recuento de valores ausentes por columna.
- Tabla de Excel con filtros, primera fila inmovilizada, encabezado destacado,
  cuerpo blanco, bordes uniformes y anchos ajustados.
- Fechas con presentación `yyyy-mm-dd`.

Estos controles detectan problemas de estructura, formato y completitud. No
confirman por sí solos la veracidad ni la actualización de los datos.

## Resultado observado

En la exportación del 5 de noviembre de 2026 se obtuvieron 29 registros y los
siete campos previstos, sin valores ausentes en esas columnas. Se comprobó que
los identificadores eran únicos, que el orden de los contratos era descendente y
que contratos y nacimientos se guardaban como fechas reales.

Durante el desarrollo se corrigió una extracción incorrecta del nombre:
pertenece a la relación `player`, no al nivel principal del registro. También se
ajustó el formato de fechas para visualizarlo correctamente en Numbers.

El contraste documentado con fuentes oficiales del club y las comprobaciones
específicas de contratos siguen pendientes. Los ajustes manuales guardados en
Numbers no forman parte de la exportación automática de Python.

## Estructura del proyecto

```text
futbol-datos/
├── src/
│   ├── first_test.py
│   ├── first_request.py
│   ├── find_team.py
│   ├── get_squad.py
│   └── export_squad.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

Durante la ejecución se crean estas carpetas locales, excluidas de Git:

- `data/raw/`: respuesta JSON y contexto de cada consulta.
- `outputs/`: archivos Excel generados y posibles revisiones locales en Numbers.

`data/processed/` queda reservada para futuras transformaciones; el flujo actual
no escribe en ella. Los entornos virtuales y las cachés también se excluyen.

## Preparación del entorno

Requisitos: Python 3.12 y una cuenta de Sportmonks con acceso a los datos del
equipo consultado. Las dependencias fijadas corresponden al entorno utilizado
durante el desarrollo.

Desde la raíz del proyecto, en macOS o Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Editar `.env` y sustituir el marcador por un token propio:

```dotenv
SPORTMONKS_API_TOKEN=YOUR_TOKEN
```

El archivo `.env` es local y está excluido de Git.

## Ejecución

Consultar las competiciones accesibles:

```bash
python src/first_request.py
```

Buscar el identificador del Celtic:

```bash
python src/find_team.py
```

Consultar la versión básica de su plantilla:

```bash
python src/get_squad.py
```

Consultar y exportar los siete campos:

```bash
python src/export_squad.py
```

En `src/export_squad.py`, la configuración del equipo se encuentra al principio:

```python
TEAM_ID = 53
TEAM_NAME = "Celtic"
```

`TEAM_ID` determina el equipo solicitado y el nombre de los archivos.
`TEAM_NAME` es una etiqueta descriptiva; no realiza la búsqueda del
identificador ni valida su correspondencia. Los scripts exploratorios
`find_team.py` y `get_squad.py` siguen configurados específicamente para Celtic.

Los archivos generados siguen este patrón:

```text
data/raw/squad_team_{TEAM_ID}_{run_id}.json
outputs/squad_team_{TEAM_ID}_{run_id}.xlsx
```

`run_id` contiene una marca de tiempo en UTC compartida por los dos archivos. La
fecha de consulta indica cuándo se obtuvo la respuesta, no cuándo se actualizó
cada dato en el proveedor.

## Revisión del código

```bash
python -m ruff check src
python -m ruff format --check src
```

Estos comandos revisan el código y su formato. No realizan peticiones a la API
ni validan los hechos deportivos.

## Limitaciones

- La cobertura y los datos accesibles dependen de la suscripción del proveedor.
- Los contratos requieren contraste adicional y pueden contener datos ausentes o
  desactualizados.
- No se dispone de representantes ni valoraciones de mercado verificados.
- Posición detallada, edad calculada, inicio del contrato, altura, peso y pie
  preferido todavía no se exportan.
- No hay base de datos, actualización programada ni interfaz para usuarios.
- El prototipo no demuestra cobertura mundial ni constituye un servicio para una
  agencia.
- El repositorio publica código y documentación; los datos descargados y los
  archivos generados se conservan localmente. Compartir esos datos requiere
  comprobar las condiciones aplicables del proveedor.

## Próximos pasos

- Documentar el contraste de la plantilla con la fuente oficial del club.
- Verificar una muestra de contratos con anuncios oficiales y registrar las
  discrepancias y la precisión de la evidencia.
- Evaluar las ampliaciones de campos según las búsquedas que deban resolverse.
- Confirmar una fuente adecuada y las condiciones de acceso a representantes y
  valoraciones.
- Preparar una propuesta con resultados demostrados, datos pendientes, costes y
  alcance de un posible piloto profesional.

## Documentación

- [Plantilla por identificador de equipo](https://docs.sportmonks.com/v3/endpoints-and-entities/endpoints/team-squads/get-team-squad-by-team-id)
- [Datos y relaciones de un jugador](https://docs.sportmonks.com/v3/endpoints-and-entities/endpoints/players/get-player-by-id)
- [Autenticación de Sportmonks](https://docs.sportmonks.com/v3/welcome/authentication)
- [pandas: exportación a Excel](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_excel.html)
- [openpyxl: tablas](https://openpyxl.readthedocs.io/en/stable/worksheet_tables.html)
- [openpyxl: estilos](https://openpyxl.readthedocs.io/en/stable/styles.html)
