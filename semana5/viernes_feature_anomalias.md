# Semana 5 — Viernes: detección y notificación de anomalías

## Objetivo

Implementar una feature vertical en SensorHub: cada sensor configura un umbral de anomalía; al registrar una lectura que lo supera, el sistema persiste una alerta consultable mediante API.

La actividad debía demostrar:

- desarrollo guiado por TDD;
- una estrategia de alerta intercambiable aplicando OCP;
- trazabilidad del uso de IA;
- validación técnica de la entrega.

## Alcance implementado

La funcionalidad quedó integrada en las capas existentes de SensorHub:

```text
HTTP → Router → Service → Repository → SQLAlchemy → Base de datos
```

Se incorporó:

- `threshold` configurable por sensor;
- validación de la configuración del umbral;
- detección de anomalías al registrar lecturas nuevas;
- persistencia de alertas;
- `GET /alerts` para consultar alertas;
- una estrategia intercambiable de alertas.

No se agregaron correo electrónico, Slack, SMS, WebSockets, colas ni múltiples canales simultáneos, porque no eran requisitos de la actividad.

## Decisiones de diseño

### Rango operativo y umbral son conceptos distintos

`min_value` y `max_value` conservan su responsabilidad: definir el rango operativo válido de una lectura.

`threshold` representa el punto a partir del cual una lectura válida se considera anómala. No se reutilizaron `min_value` o `max_value` como umbral porque una lectura fuera del rango operativo actual se rechaza y no podría generar una alerta persistida.

La regla de configuración quedó definida como:

```text
min_value <= threshold < max_value
```

Esto garantiza que el umbral esté dentro del rango operativo y que exista al menos una lectura válida que pueda superarlo.

### Contrato de una alerta

Cada alerta conserva:

- `sensor_id`;
- `reading_id`;
- `reading_value`;
- `threshold`;
- `created_at`.

Guardar el valor leído y el umbral como instantáneas permite explicar por qué se generó la alerta incluso si la lectura o la configuración del sensor cambian posteriormente.

### Strategy y OCP

Se definió `AlertStrategy` como una abstracción con la operación `handle_anomaly(reading, threshold)`.

La implementación actual, `DatabaseAlertStrategy`, delega la persistencia a `AlertRepository`. Por ello, `ReadingService` decide cuándo existe una anomalía, pero no necesita conocer SQLAlchemy, la tabla `alerts` ni una tecnología concreta de notificación.

```text
ReadingService
    ↓
AlertStrategy
    ↑
DatabaseAlertStrategy
    ↓
AlertRepository
    ↓
AlertModel
```

Una futura estrategia, como email o Slack, podría implementar el mismo contrato sin modificar `ReadingService`.

### Migración de datos existentes

Para sensores existentes se eligió la política temporal:

```text
threshold = min_value + 0.8 * (max_value - min_value)
```

La regla de anomalía es de límite superior (`value > threshold`), por lo que el 80% del rango representa una advertencia preventiva más apropiada que el punto medio. Los sensores nuevos continúan recibiendo su umbral explícitamente por API.

## TDD y evidencia

El desarrollo se realizó mediante ciclos pequeños.

### 1. Estrategia de alerta

Se escribió `test_record_handles_anomaly_when_value_exceeds_sensor_threshold`.

El test inició en RED porque `ReadingService` no aceptaba `alert_strategy`:

```text
TypeError: ReadingService.__init__() takes 3 positional arguments but 4 were given
```

Se llevó a GREEN agregando la dependencia, conservando el sensor validado y notificando a la estrategia solo después de persistir la lectura.

### 2. Persistencia del threshold

Se escribió `test_create_sensor_persists_threshold`.

El test inició en RED con:

```text
KeyError: 'threshold'
```

La API todavía ignoraba el campo. Se agregó el umbral a modelo, schema, validación de dominio, servicio, router y fixtures.

### 3. Alerta consultable por API

Se escribió `test_reading_above_threshold_creates_queryable_alert`.

El test inició en RED porque la estrategia no estaba inyectada desde el router:

```text
TypeError: ReadingService.__init__() missing 1 required positional argument: 'alert_strategy'
```

Se implementaron `AlertModel`, `AlertRepository`, `DatabaseAlertStrategy`, `AlertService`, las dependencias de router y `GET /alerts`. El test quedó en GREEN.

### 4. Caso de frontera

Se agregó `test_reading_at_threshold_does_not_create_alert` para documentar que:

```text
value == threshold
```

no genera una alerta.

Esta prueba se añadió después como regresión explícita del contrato `>`; no se presenta como un ciclo RED inicial.

## Prompts principales y resultados

### Prompt de análisis inicial

Se pidió a la IA inspeccionar `models.py`, `repositories.py`, `services.py`, `schemas.py` y `routers.py` antes de implementar cambios, y diseñar una solución mínima que respetara TDD, Strategy/OCP y la arquitectura por capas.

Resultado:

- se separó `threshold` de `min_value` y `max_value`;
- se decidió persistir alertas;
- se ubicó cada responsabilidad en su capa;
- se evitó introducir canales de notificación no solicitados.

### Prompt de migración en Codex para VS Code

Se pidió a Codex crear únicamente una revisión Alembic que:

- agregara `sensors.threshold`;
- rellenara sensores existentes con la política del 80%;
- creara `alerts` con claves foráneas en cascada e índices;
- incluyera `downgrade()`;
- fuera compatible con SQLite y PostgreSQL;
- no modificara otros archivos, ejecutara migraciones ni hiciera commits.

Resultado:

- Codex creó únicamente `a1c7e3f9b2d4_add_sensor_threshold_and_alerts.py`.
- La revisión fue inspeccionada y aprobada antes de ejecutarse.
- No se aceptó código generado sin revisión.

## Uso responsable de IA

La IA se utilizó como apoyo para:

- analizar la arquitectura;
- formular tests pequeños;
- explicar Strategy, OCP y migraciones;
- diagnosticar errores de inyección, schemas, fixtures, Pytest y Alembic;
- generar de forma acotada la migración Alembic.

Las decisiones humanas fueron:

- definir el significado del umbral;
- elegir la política del 80% para datos heredados;
- seleccionar los campos de `Alert`;
- limitar el alcance a persistencia y API;
- aceptar la estrategia de base de datos;
- revisar la migración antes de aplicarla;
- verificar resultados mediante pruebas y herramientas de calidad.

Durante la transcripción de cambios se generó accidentalmente un constructor duplicado en `ReadingService`. Se corrigió de forma acotada y se verificó la sintaxis antes de continuar. Esto reforzó la necesidad de revisar cambios de IA o fragmentos copiados antes de ejecutar la suite.

## Problemas encontrados y resolución

- Algunos archivos no se habían guardado; se guardaron antes de volver a ejecutar las pruebas.
- Faltaba inyectar `alert_strategy` en `ReadingService` y en su fábrica del router.
- Varios fixtures construían sensores sin `threshold`; se actualizaron para reflejar el nuevo contrato.
- La ejecución directa de `pytest` no resolvía imports de `semana2`; se utilizó `python -m pytest`.
- Pytest no pudo usar su carpeta temporal predeterminada por permisos de Windows; se usó `--basetemp`.
- La base SQLite existente no coincidía exactamente con el historial de Alembic. Se preservó como respaldo en `sensorhub.pre-migration-backup-20260815-160150.db` y se reconstruyó una base local nueva desde las migraciones.
- La base nueva quedó validada con `alembic check`.

## Archivos principales involucrados

- `app/models.py`
- `app/domain.py`
- `app/schemas.py`
- `app/services.py`
- `app/repositories.py`
- `app/routers.py`
- `tests/test_sensors.py`
- `tests/test_services.py`
- `tests/test_main.py`
- `migrations/versions/a1c7e3f9b2d4_add_sensor_threshold_and_alerts.py`
- `semana5/viernes_feature_anomalias.md`

## Verificación final

- `103 passed`.
- Cobertura global: `96.04%`.
- Ruff: sin errores.
- mypy: sin errores.
- Alembic: `a1c7e3f9b2d4 (head)`.
- `alembic check`: sin operaciones pendientes.
- Se mantuvo una advertencia externa de `httpx`/`TestClient`; no se modificó porque no pertenece al alcance de esta feature.

## Conclusión

La feature quedó implementada desde el modelo de datos hasta la API. El ejercicio mostró que una IA puede acelerar análisis, diagnóstico y tareas mecánicas, pero no sustituye el criterio de ingeniería.

La entrega se mantuvo deliberadamente pequeña: un umbral por sensor, una alerta persistida y una estrategia intercambiable. Las decisiones se revisaron con evidencia: tests, cobertura, análisis estático y migraciones verificadas.