# AI Log — Integrador Semana 3

## 2026-08-01

Se utilizó Codex para apoyar la revisión e implementación del integrador de
SensorHub. El trabajo se realizó sobre una línea base limpia de 62 pruebas y
96.20 % de cobertura.

### Decisiones y cambios

- Se agregó `SensorModel` como entidad persistente y una clave foránea desde
  `ReadingModel`.
- Se implementó CRUD REST completo de sensores.
- Se aceptan únicamente `temperature` con `C` y `humidity` con `%`.
- `min_value` y `max_value` se documentaron como una decisión adicional para
  representar el rango operativo, no umbrales de anomalía.
- Las lecturas requieren un sensor existente, unidad coincidente y valor dentro
  del rango inclusivo.
- Se conservaron las rutas anteriores de lecturas por compatibilidad.
- La presentación se separó en `routers.py` y los esquemas Pydantic en
  `schemas.py`; `main.py` quedó dedicado a crear y configurar FastAPI.
- No se incorporaron simuladores, alertas ni detección de anomalías de Semana 2.

### Método de trabajo

Se comprobó una línea base con pytest, Ruff y mypy; se escribieron pruebas que
fallaron porque `/sensors` no existía; se implementó la funcionalidad mínima; y
se repitieron pruebas y análisis estático antes de documentar.

La revisión humana debe concentrarse en comprender las reglas de servicio, la
inyección de repositorios y el contrato REST antes de guardar los cambios.

### Correcciones posteriores a revisión

- Las reglas y tipos compartidos se movieron a `app/domain.py`; los servicios
  dejaron de importar esquemas Pydantic.
- `ReadingService` exige explícitamente repositorios de lecturas y sensores.
- Los cambios de configuración se contrastan con el historial: tipo y unidad
  quedan bloqueados tras la primera lectura y el rango debe conservar todas las
  mediciones. Los conflictos con estado persistido se traducen a HTTP 409.
- SQLite activa claves foráneas en cada conexión y usa borrado en cascada.

# Semana 4 — Docker, CI/CD y despliegue

## 2026-08-10

Durante la Semana 4 se preparó SensorHub para ejecutarse y desplegarse mediante
un flujo de entrega más cercano a un entorno de producción.

### Docker y PostgreSQL

- Se creó un Dockerfile basado en `python:3.12-slim`.
- Se ordenaron las instrucciones para reutilizar la caché de dependencias.
- Se utilizó `.dockerignore` para excluir archivos locales y temporales.
- Se configuró Docker Compose con los servicios `api` y `db`.
- PostgreSQL 16 se utiliza como base de datos dentro de Compose.
- La configuración se obtiene mediante variables de entorno.
- Dentro de la red de Compose la API se conecta al host `db`, correspondiente
  al nombre del servicio PostgreSQL.
- Se agregó un healthcheck a PostgreSQL para evitar que la API intente conectarse
  antes de que la base esté disponible.

### Migraciones

- Se incorporó Alembic para gestionar los cambios de esquema.
- La creación automática de tablas dejó de depender de `create_all`.
- El contenedor ejecuta `alembic upgrade head` antes de iniciar Uvicorn.
- Se creó una migración inicial para las tablas `sensors` y `readings`.

### Integración continua

- Se creó un workflow de GitHub Actions que se ejecuta en pushes a `main` y
  pull requests.
- El pipeline ejecuta Ruff, mypy y pytest con el requisito de cobertura del proyecto.
- Se provocó intencionalmente una falla para comprobar que el pipeline detectara
  errores y posteriormente se corrigió.
- El estado del CI se muestra mediante un badge en el README.

### Despliegue continuo

- Se configuró Render mediante `render.yaml`.
- Render ejecuta la API dentro de Docker y utiliza PostgreSQL administrado.
- `DATABASE_URL` se obtiene desde la base de datos configurada en Render.
- El servicio utiliza `/health` como healthcheck.
- Un merge a `main`, correspondiente al commit `557f966`, activó GitHub Actions
  y posteriormente un nuevo despliegue automático en Render, demostrando CD.

### Seguridad y documentación

- `.env` permanece fuera del historial mediante `.gitignore`.
- `.env.example` documenta únicamente valores locales de ejemplo.
- Se revisó el historial completo con Gitleaks y no se detectaron secretos.
- El README se actualizó con instrucciones de Docker Compose, badge de CI,
  URLs públicas y advertencias sobre eliminación de volúmenes.

### Uso de IA

La IA se utilizó como apoyo para explicar Docker, Compose, Alembic, CI/CD y
Render; revisar configuraciones; diagnosticar errores y preparar verificaciones.
Las decisiones se validaron mediante ejecución local, pruebas automatizadas,
GitHub Actions, revisión de Git y comprobación del despliegue público antes de
integrar los cambios.