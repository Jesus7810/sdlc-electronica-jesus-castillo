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
