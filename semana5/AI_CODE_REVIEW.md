# AI Code Review — SensorHub

## Objetivo

Realizar una revisión de código asistida por IA sobre `ReadingService`, evaluando:

- principios SOLID y separación de responsabilidades;
- casos borde;
- seguridad;
- rendimiento.

La revisión fue realizada con Codex. Las recomendaciones de la IA no se aceptaron automáticamente: cada hallazgo fue contrastado con el código y evaluado antes de decidir si implementarlo o rechazarlo para esta actividad.

## Clase revisada

`ReadingService` en `app/services.py`.

Esta clase contiene parte de la lógica de negocio relacionada con las lecturas de sensores, incluyendo:

- validación del sensor;
- validación de unidad y rango;
- registro de lecturas;
- consulta y filtrado;
- actualización;
- eliminación.

## Hallazgos

### 1. Condición de carrera entre validación del sensor e inserción

**Ubicación:** `ReadingService.record()`.

**Severidad propuesta por IA:** alta.

Codex señaló que el sensor podría cambiar de tipo, unidad o rango entre la validación de una lectura y su inserción en la base de datos.

**Corrección propuesta por IA:** hacer atómica la validación y la inserción mediante una transacción y bloquear la fila del sensor durante ambas operaciones.

**Decisión:** rechazado para esta actividad / pospuesto.

El riesgo es técnicamente válido, pero solucionarlo correctamente requeriría definir una estrategia transaccional y posiblemente utilizar bloqueo de filas. Esto introduce conceptos de concurrencia y aislamiento que exceden el alcance de esta actividad.

No se implementó una solución únicamente para satisfacer la recomendación de la IA.

---

### 2. Mezcla de fechas naïve y aware

**Ubicación:** `ReadingService.list()`.

**Severidad propuesta por IA:** media.

`ReadingService.list()` comparaba directamente `from_date` y `to_date`.

Python no permite comparar directamente un `datetime` con zona horaria (`aware`) con uno sin zona horaria (`naïve`), por lo que una combinación de ambos podía producir un `TypeError` y terminar como un error HTTP 500.

**Corrección propuesta por IA:** establecer una convención temporal única, normalizando las fechas o rechazando explícitamente la mezcla de datetimes naïve y aware mediante un error controlado.

**Decisión:** aceptado e implementado.

Se agregó una validación explícita que detecta cuando una fecha es naïve y la otra aware y lanza `InvalidDateRangeError`.

La API transforma este error en una respuesta controlada HTTP 400.

---

### 3. Regla del cero absoluto aplicada a todos los sensores

**Ubicación:** `ReadingService.record()`, `ReadingService.update()` y validación en `_validate_for_sensor()`.

**Severidad propuesta por IA:** media.

La comprobación:

`value < -273.15`

se realizaba antes de conocer el tipo del sensor, por lo que una regla física específica de temperatura también se aplicaba a sensores de humedad.

**Corrección propuesta por IA:** aplicar la regla del cero absoluto únicamente cuando el sensor sea de tipo `temperature`, o eliminarla si el rango configurado del sensor debe ser la única autoridad.

**Decisión:** aceptado e implementado.

La validación se movió a `_validate_for_sensor()` y ahora únicamente se aplica cuando:

`sensor.type == "temperature"`

Esto permite que cada tipo de sensor sea validado según las reglas que realmente le corresponden y evita duplicar la comprobación entre `record()` y `update()`.

---

### 4. Dependencia de `ReadingService` respecto a `IntegrityError`

**Ubicación:** `ReadingService.record()` y la dependencia de `sqlalchemy.exc.IntegrityError`.

**Severidad propuesta por IA:** media.

Codex señaló que la capa de servicio conoce directamente `sqlalchemy.exc.IntegrityError`, lo que genera acoplamiento con una tecnología concreta de persistencia.

También señaló que diferentes errores de integridad podrían terminar siendo traducidos al mismo `ReadingConflictError`.

**Corrección propuesta por IA:** trasladar al repository la interpretación de las restricciones de persistencia y exponer errores de dominio específicos al service, diferenciando por ejemplo un timestamp duplicado de una referencia a un sensor inexistente.

**Decisión:** rechazado para esta actividad / pospuesto.

El hallazgo arquitectónico es válido, pero resolverlo correctamente requeriría modificar la frontera entre repository y service y diseñar una traducción explícita de errores de persistencia a errores de dominio.

No se consideró adecuado realizar ese refactor dentro del alcance de esta actividad.

---

### 5. Consulta `exists_at()` redundante

**Ubicación:** `ReadingService.record()`.

**Severidad propuesta por IA:** baja.

Antes de insertar una lectura se consulta si ya existe otra con la misma combinación `(sensor_id, timestamp)`.

Sin embargo, la base de datos ya contiene una restricción `UNIQUE` y posteriormente se captura `IntegrityError`.

Esto introduce una consulta adicional y tampoco elimina completamente posibles condiciones de carrera.

**Corrección propuesta por IA:** eliminar la consulta previa `exists_at()` y utilizar la restricción `UNIQUE(sensor_id, timestamp)` de la base de datos como fuente de verdad para detectar el conflicto.

**Decisión:** rechazado para esta actividad / pospuesto.

La observación es técnicamente válida, pero eliminar `exists_at()` correctamente también requiere garantizar que las diferentes violaciones de integridad sean traducidas al error de dominio correspondiente.

Como este problema está relacionado con el hallazgo anterior sobre `IntegrityError`, se decidió no modificar parcialmente el flujo de persistencia sin resolver primero esa separación de responsabilidades.

---

## Seguridad

Codex no identificó una vulnerabilidad de seguridad concreta atribuible a `ReadingService`.

La clase no construye SQL dinámico, no administra credenciales y no es responsable directamente de autenticación o autorización.

Se decidió no inventar un hallazgo de seguridad únicamente para cubrir esta categoría.

## Casos borde

Después del code review se solicitó a Codex identificar casos borde que no estuvieran cubiertos por la suite existente.

Se seleccionaron casos relacionados con:

- mezcla de fechas naïve y aware;
- aplicación incorrecta del cero absoluto a humedad;
- unidad `C` utilizada en un sensor de humedad;
- `value` o `unit` nulos;
- timestamp malformado.

Se añadieron 7 ejecuciones de prueba nuevas entre pruebas de servicio y API, superando el requisito mínimo de 5 tests nuevos indicado en la actividad.

## Archivos modificados

- `app/services.py`
- `tests/test_services.py`
- `tests/test_sensors.py`
- `semana5/AI_CODE_REVIEW.md`

## Verificación

Después de los cambios se ejecutaron las pruebas y herramientas de calidad.

Resultados:

- 99 tests superados;
- cobertura: 96.27 %;
- Ruff: sin errores.

Los cambios también fueron revisados mediante `git diff` antes de prepararlos para commit.

## Conclusión

La principal lección de esta actividad fue que utilizar IA para code review no significa aceptar automáticamente todas sus recomendaciones.

Codex encontró problemas reales, pero algunas de sus correcciones implicaban cambios cuyo costo y alcance eran mayores que el beneficio inmediato para esta actividad.

El proceso utilizado fue:

problema → revisión con IA → verificación del código → evaluación humana → aceptación o rechazo → tests → verificación.

La IA permitió ampliar la cantidad de escenarios considerados, mientras que la decisión final sobre qué modificar permaneció bajo criterio humano.