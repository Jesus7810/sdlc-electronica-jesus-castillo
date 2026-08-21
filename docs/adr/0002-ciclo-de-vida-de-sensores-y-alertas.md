# ADR 0002: Ciclo de vida de sensores y alertas para SensorHub

## Estado

Aceptado.

## Contexto

SensorHub almacena telemetría y alertas asociadas a sensores. El modelo anterior
permite eliminar sensores físicamente, editar o eliminar lecturas y utiliza un
único umbral de alerta. Estas decisiones no conservan adecuadamente el historial
operativo ni permiten distinguir entre advertencias y condiciones críticas.

El sistema debe conservar la identidad, ubicación, tipo, unidad y límites físicos
de cada sensor, además de permitir desactivarlo temporalmente sin eliminar su
historial. Las lecturas deben ser hechos inmutables y sus marcas de tiempo deben
manejarse en UTC.

También se requiere separar la validez física de una lectura de su estado
operativo. Una lectura físicamente imposible no debe persistirse ni generar una
alerta; una lectura físicamente válida, pero fuera de los umbrales operativos,
debe generar o actualizar una alerta trazable.

## Decisión

Se adopta el siguiente ciclo de vida para sensores y alertas:

- Los sensores no se eliminan físicamente. Se desactivan, conservan sus lecturas
  y alertas, salen de los listados normales y pueden reactivarse.
- Un sensor desactivado no acepta nuevas lecturas. Al reactivarse se limpia
  `deactivated_at`.
- Activar o desactivar un sensor es idempotente y devuelve el sensor en su estado
  final.
- Las lecturas son inmutables. Se conserva la unicidad de
  `(sensor_id, timestamp)` y un duplicado devuelve `409 Conflict`.
- Todos los timestamps se reciben, almacenan y consultan en UTC.
- Cada sensor conserva límites físicos y define cuatro umbrales operativos que
  deben cumplir estrictamente:

  ```text
  min_value < low_critical_threshold < low_warning_threshold < high_warning_threshold < high_critical_threshold < max_value
  ```

- Una lectura fuera de `min_value` y `max_value` es físicamente inválida: se
  rechaza, no se persiste y no genera alerta.
- Una lectura dentro del intervalo inclusivo entre
  `low_warning_threshold` y `high_warning_threshold` es normal. La igualdad con
  los umbrales de advertencia sigue siendo normal.
- Una lectura menor que `low_warning_threshold` o mayor que
  `high_warning_threshold`, sin alcanzar un umbral crítico, genera una alerta
  con severidad `WARNING`.
- Una lectura menor o igual que `low_critical_threshold`, o mayor o igual que
  `high_critical_threshold`, genera una alerta con severidad `CRITICAL`.
- Cada alerta tiene una condición `low` o `high`, una severidad `WARNING` o
  `CRITICAL`, y un estado `open`, `acknowledged` o `resolved`.
- Las alertas `open` y `acknowledged` se consideran no resueltas. Solo puede
  existir una alerta no resuelta por combinación de sensor y condición.
- Una lectura de mayor severidad para una condición con alerta no resuelta
  actualiza o escala la alerta existente, sin crear un duplicado. Si una alerta
  `acknowledged` escala a `CRITICAL`, vuelve a `open` y conserva evidencia de su
  reconocimiento previo.
- Las alertas se resuelven manualmente. Una lectura normal no cierra una alerta.
  Solo una alerta `resolved` permite crear una nueva alerta futura para la misma
  condición.
- Las alertas conservan como hecho histórico la lectura, el umbral, la condición
  y la severidad que las originaron, aunque la configuración posterior del sensor
  cambie.
- Las estadísticas por sensor incluyen el historial de sensores desactivados.
- `/health` comprueba la disponibilidad de la aplicación y de la base de datos.
  `/metrics` expone sensores activos, lecturas registradas y alertas no resueltas
  (`open` y `acknowledged`).
- Aunque la base local no contiene datos, los cambios de esquema se aplicarán con
  migraciones Alembic para que Docker, PostgreSQL y producción reproduzcan el
  mismo esquema.

## Consecuencias

### Positivas

- Se conserva el historial de telemetría y alertas al desactivar sensores, lo que
  evita la pérdida de evidencia asociada al borrado físico.
- La separación entre límites físicos y umbrales operativos permite rechazar datos
  imposibles sin ocultar condiciones operativas anómalas válidas.
- Los niveles `WARNING` y `CRITICAL` permiten priorizar la atención de alertas.
- La restricción de una alerta no resuelta por sensor y condición reduce el ruido
  producido por lecturas anómalas repetidas.
- La evidencia de origen y de reconocimiento conserva la trazabilidad cuando una
  alerta escala o cuando los umbrales del sensor cambian.
- UTC evita ambigüedades al consultar lecturas, estadísticas y alertas por rango
  temporal.
- Las migraciones Alembic hacen reproducible la evolución del esquema entre los
  entornos locales y de producción.

### Negativas

- El modelo de datos, las validaciones y los contratos HTTP requieren más campos
  y reglas que el esquema de umbral único.
- Las rutas de edición y eliminación de lecturas dejan de formar parte del
  contrato público, por lo que los clientes y pruebas existentes deben adaptarse.
- La desactivación obliga a definir filtros explícitos para diferenciar listados
  normales de consultas históricas.
- La deduplicación y el escalamiento de alertas requieren coordinación
  transaccional y pruebas de concurrencia.
- El uso obligatorio de UTC exige validar timestamps de entrada y adaptar las
  consultas existentes que usan fechas sin zona horaria.

## Alternativas descartadas

### Borrado físico de sensores

Se descarta porque elimina o deja sin contexto lecturas y alertas históricas, e
impide reactivar un sensor con la misma identidad y configuración.

### Un único umbral operativo

Se descarta porque no diferencia entre desviaciones de advertencia y situaciones
críticas, ni permite representar condiciones bajas y altas de forma explícita.

### Resolución automática con una lectura normal

Se descarta porque una lectura aislada normal no demuestra que la condición haya
sido revisada o corregida. La resolución manual conserva responsabilidad y
trazabilidad operacional.

### Permitir alertas no resueltas duplicadas

Se descarta porque múltiples lecturas de una misma condición producirían ruido y
dificultarían conocer el estado operativo real del sensor.

### Omitir migraciones por tener una base local vacía

Se descarta porque el esquema debe poder evolucionar y reproducirse de forma
controlada en Docker, PostgreSQL y producción.
