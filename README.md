# SensorHub API

Proyecto desarrollado durante el programa **EDSIA — De Electrónica a Desarrollo de Software con IA**.

SensorHub es una API REST para administrar sensores y sus lecturas. Está construida con FastAPI, SQLAlchemy y SQLite, aplicando arquitectura por capas, inyección de dependencias, principios SOLID y pruebas automatizadas.

## Objetivo del proyecto

El objetivo es construir progresivamente un sistema de monitoreo de sensores con prácticas profesionales de desarrollo de software:

- Código claro y mantenible.
- Separación de responsabilidades.
- Persistencia de datos.
- API REST.
- Desarrollo guiado por pruebas.
- Control de calidad automatizado.
- Uso profesional de Git y GitHub.

## Arquitectura

La aplicación utiliza una arquitectura por capas:

```text
Cliente HTTP
     ↓
Routers de FastAPI
     ↓
SensorService / ReadingService
     ↓
SensorRepository / ReadingRepository
     ↓
Repositorios SQLAlchemy
     ↓
Base de datos SQLite
```

### Responsabilidades

- **Endpoints:** reciben solicitudes HTTP, validan el formato de entrada y generan respuestas HTTP.
- **Servicio:** contiene las reglas de negocio y coordina las operaciones.
- **Contrato de repositorio:** define las operaciones de persistencia que necesita el servicio.
- **Repositorio SQLAlchemy:** implementa el contrato y realiza las operaciones sobre la base de datos.
- **Modelos:** representan las entidades almacenadas en SQLite.

Esta separación permite cambiar la tecnología de almacenamiento sin modificar las reglas de negocio.

## Estructura principal

```text
app/
├── __init__.py
├── database.py
├── main.py
├── models.py
├── schemas.py
├── repositories.py
├── routers.py
└── services.py

tests/
├── test_main.py
└── test_services.py
```

## Tecnologías utilizadas

- Python 3.13
- FastAPI
- Pydantic
- SQLAlchemy 2.x
- SQLite
- Uvicorn
- pytest
- pytest-cov
- Ruff
- mypy
- Git y GitHub

## Requisitos

Para ejecutar el proyecto se necesita:

- Python 3.13 o una versión compatible.
- Git.
- Un entorno virtual de Python.

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU-USUARIO/sdlc-electronica-jesus-castillo.git
cd sdlc-electronica-jesus-castillo
```

### 2. Crear un entorno virtual

```bash
python -m venv .venv
```

### 3. Activar el entorno virtual

En Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

En Linux o macOS:

```bash
source .venv/bin/activate
```

### 4. Instalar las dependencias

```bash
python -m pip install -r requirements.txt
```

## Ejecución

Iniciar el servidor de desarrollo:

```bash
python -m uvicorn app.main:app --reload
```

La API estará disponible en:

```text
http://127.0.0.1:8000
```

FastAPI genera documentación interactiva automáticamente:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

Al iniciar la aplicación se crean automáticamente las tablas necesarias en la base de datos local `sensorhub.db`.

## Endpoints

| Método | Ruta | Descripción | Respuesta exitosa |
|---|---|---|---|
| `GET` | `/health` | Comprueba el estado de la API | `200 OK` |
| `POST` | `/sensors` | Crea un sensor | `201 Created` |
| `GET` | `/sensors` | Lista los sensores | `200 OK` |
| `GET` | `/sensors/{sensor_id}` | Consulta un sensor | `200 OK` |
| `PATCH` | `/sensors/{sensor_id}` | Actualiza parcialmente un sensor | `200 OK` |
| `DELETE` | `/sensors/{sensor_id}` | Elimina un sensor | `204 No Content` |
| `POST` | `/sensors/{sensor_id}/readings` | Registra una lectura (canónica) | `201 Created` |
| `GET` | `/sensors/{sensor_id}/readings` | Lista, filtra y pagina (canónica) | `200 OK` |
| `POST` | `/readings` | Ruta anterior conservada por compatibilidad | `201 Created` |
| `GET` | `/readings` | Ruta anterior conservada por compatibilidad | `200 OK` |
| `GET` | `/readings/{reading_id}` | Obtiene una lectura por ID | `200 OK` |
| `PATCH` | `/readings/{reading_id}` | Actualiza parcialmente una lectura | `200 OK` |
| `DELETE` | `/readings/{reading_id}` | Elimina una lectura | `204 No Content` |

Cuando una lectura no existe, los endpoints correspondientes devuelven:

```json
{
  "detail": "Lectura no encontrada"
}
```

con el código HTTP `404 Not Found`.

## Sensores y rango operativo

Antes de registrar lecturas se crea el sensor:

```http
POST /sensors
Content-Type: application/json
```

```json
{
  "id": "TEMP-01",
  "name": "Temperatura del laboratorio",
  "type": "temperature",
  "unit": "C",
  "min_value": -40,
  "max_value": 125
}
```

Los tipos iniciales y sus unidades son deliberadamente mínimos:

| Tipo | Unidad aceptada |
|---|---|
| `temperature` | `C` |
| `humidity` | `%` |

`min_value` y `max_value` son una decisión adicional del proyecto: representan
el rango físico u operativo configurado para aceptar una medición y no un umbral
de anomalía. Debe cumplirse `min_value < max_value`. No se incluyen simuladores,
alertas ni detección de anomalías en este integrador.

La actualización de sensores es parcial. Por ejemplo:

```json
{
  "name": "Cámara fría",
  "min_value": -80
}
```

Si el sensor todavía no tiene lecturas, su tipo y unidad pueden cambiar juntos
si la configuración final es compatible. Cuando ya tiene historial, un cambio
efectivo de tipo o unidad devuelve `409 Conflict`; reenviar el valor actual sí
es válido. Los límites pueden cambiar únicamente cuando todas las lecturas
existentes siguen dentro del nuevo intervalo inclusivo. El historial nunca se
modifica ni elimina para hacer posible un PATCH.

## Crear una lectura

Solicitud:

```http
POST /sensors/TEMP-01/readings
Content-Type: application/json
```

Cuerpo:

```json
{
  "value": 25.5,
  "unit": "C",
  "timestamp": "2026-07-30T12:00:00"
}
```

Ejemplo de respuesta:

```json
{
  "sensor_id": "TEMP-01",
  "value": 25.5,
  "unit": "C",
  "id": 1,
  "timestamp": "2026-07-30T12:00:00"
}
```

El `sensor_id` se obtiene exclusivamente de la ruta. `timestamp` es opcional y,
si se omite, el servicio lo genera automáticamente. La combinación de sensor y fecha
es única: intentar registrar dos lecturas del mismo sensor en el mismo instante
devuelve `409 Conflict`; repetir un valor en fechas distintas es válido.

Antes de guardar, `ReadingService` comprueba que el sensor exista, que la unidad
coincida y que `min_value <= value <= max_value`. Una lectura rechazada no llega
al repositorio y, por tanto, no se persiste.

## Listar lecturas

```http
GET /sensors/TEMP-01/readings
```

El endpoint admite los siguientes parámetros de consulta:

| Parámetro | Descripción | Valor predeterminado |
|---|---|---|
| `limit` | Cantidad máxima de resultados, entre 1 y 100 | `50` |
| `offset` | Cantidad de registros que se omiten | `0` |
| `from` | Fecha inicial inclusiva en formato ISO 8601 | Sin límite |
| `to` | Fecha final inclusiva en formato ISO 8601 | Sin límite |

Ejemplo:

```http
GET /sensors/TEMP-01/readings?from=2026-07-01T00:00:00&to=2026-07-31T23:59:59&offset=0&limit=5
```

Si `from` es posterior a `to`, la API devuelve `400 Bad Request`.
Fechas mal formadas, `limit` fuera de 1–100 u `offset` negativo devuelven
`422 Unprocessable Entity`.

## Consultar una lectura

```http
GET /readings/1
```

Devuelve la lectura correspondiente al identificador indicado o una respuesta `404` si no existe.

## Actualizar una lectura

La actualización es parcial, por lo que solamente se envían los campos que se desean modificar:

```http
PATCH /readings/1
Content-Type: application/json
```

```json
{
  "value": 30.0
}
```

Los campos editables son:

- `value`
- `unit`

El campo `sensor_id` no se modifica mediante este endpoint.

Si el dato tiene un formato válido, pero viola una regla de negocio, la API devuelve `400 Bad Request`. Por ejemplo, una temperatura inferior al cero absoluto.

## Códigos de error

- `400 Bad Request`: regla de negocio o intervalo de fechas inválido.
- `404 Not Found`: la lectura solicitada no existe.
- `409 Conflict`: ya existe una lectura del mismo sensor con igual `timestamp`.
- `409 Conflict`: también se usa al crear un sensor con un ID existente.
- `422 Unprocessable Entity`: cuerpo, fecha o paginación con formato inválido.

## Eliminar una lectura

```http
DELETE /readings/1
```

Si la lectura se elimina correctamente, la API devuelve `204 No Content`. Si el identificador no existe, devuelve `404 Not Found`.

En producción, esta operación debe protegerse mediante autorización,
deshabilitarse o sustituirse por borrado lógico de acuerdo con las reglas y
requisitos de auditoría del sistema.

## Base de datos

El proyecto utiliza SQLite como sistema de persistencia.

Cada conexión activa `PRAGMA foreign_keys=ON`. La clave foránea de lecturas usa
`ON DELETE CASCADE`, por lo que eliminar un sensor elimina sus lecturas. Una base
creada con una versión anterior del modelo requiere una migración Alembic para
incorporar físicamente esta restricción; `create_all` no altera tablas existentes.

La configuración se encuentra en `app/database.py` y la base local se almacena en:

```text
sensorhub.db
```

Las pruebas no utilizan esta base de datos real. En su lugar, crean una base SQLite temporal en memoria para mantener cada prueba aislada y evitar modificar los datos locales.

## Pruebas automatizadas

El proyecto contiene:

- Pruebas unitarias de la capa de servicio.
- Pruebas del repositorio.
- Pruebas de integración de la API.
- Pruebas de respuestas exitosas.
- Pruebas de errores `400`, `404`, `409` y `422`.
- Pruebas de filtrado y paginación.
- Pruebas de actualización y eliminación.

Ejecutar todas las pruebas:

```bash
python -m pytest -v
```

El proyecto exige una cobertura mínima de 80 %.

## Control de calidad

### Ruff

Comprueba el estilo del código, los imports y posibles errores:

```bash
python -m ruff check app tests
```

### mypy

Realiza la comprobación estática de tipos:

```bash
python -m mypy app tests
```

### pytest

Ejecuta las pruebas y calcula la cobertura:

```bash
python -m pytest -v
```

Antes de considerar terminado un cambio deben pasar las tres verificaciones.

## Prácticas aplicadas

Durante el desarrollo se han aplicado:

- Arquitectura por capas.
- Inyección de dependencias.
- Principio de responsabilidad única.
- Inversión de dependencias.
- Patrón repositorio.
- Capa de servicio.
- Validación con Pydantic.
- Persistencia con SQLAlchemy.
- Pruebas unitarias y de integración.
- Desarrollo guiado por pruebas.
- Commits pequeños y descriptivos.
- Definition of Done con calidad automatizada.

## Estado actual

Actualmente, SensorHub permite:

- Crear, listar, consultar, actualizar y eliminar sensores.
- Validar compatibilidad entre tipo y unidad.
- Validar lecturas contra el rango operativo del sensor.
- Relacionar sensores y lecturas mediante clave foránea.
- Registrar lecturas.
- Consultar todas las lecturas.
- Filtrar lecturas por sensor.
- Paginar los resultados.
- Consultar una lectura por ID.
- Actualizar parcialmente una lectura.
- Eliminar una lectura.
- Validar reglas de negocio.
- Persistir información en SQLite.
- Probar la API sin modificar la base de datos real.

## Autor

**Jesús Roberto Castillo López**

Estudiante de Ingeniería en Instrumentación Electrónica y participante del programa **EDSIA — De Electrónica a Desarrollo de Software con IA**.
