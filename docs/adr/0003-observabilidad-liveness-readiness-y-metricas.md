# ADR 0003: Observabilidad, liveness, readiness y métricas para SensorHub

## Estado

Aceptado.

## Contexto

SensorHub necesita señales operativas útiles tanto para un despliegue como para
la supervisión local. La disponibilidad del proceso HTTP y la disponibilidad de
la base de datos son estados distintos: un proceso puede responder solicitudes
mientras la base de datos está temporalmente inaccesible.

El ADR 0002 indicó que `/health` comprueba la aplicación y la base de datos. Esa
afirmación se sustituye únicamente por esta decisión de observabilidad. Se
mantienen sin cambios las decisiones de dominio, ciclo de vida y métricas de
negocio definidas en el ADR 0002.

También se requiere exponer conteos operativos sin cargar entidades completas ni
revelar al cliente información sensible de errores de infraestructura.

## Decisión

Se adoptan tres endpoints con responsabilidades separadas:

- `/health` es el endpoint de **liveness**. Devuelve `200 {"status":"ok"}` si
  el proceso HTTP puede responder y no consulta la base de datos.
- `/ready` es el endpoint de **readiness**. Comprueba la disponibilidad de la
  base de datos mediante una operación mínima. Devuelve
  `200 {"status":"ready"}` cuando está disponible y
  `503 {"status":"unavailable"}` ante una indisponibilidad de infraestructura.
- `/metrics` expone métricas de solo lectura en Prometheus text format. Incluye
  las gauges `sensorhub_active_sensors`,
  `sensorhub_registered_readings` y `sensorhub_unresolved_alerts`.

Las métricas se calculan en la base de datos con conteos agregados. Un sensor
activo es aquel con `is_active = true`; las lecturas registradas incluyen todas
las filas de lecturas; y las alertas no resueltas incluyen los estados `open` y
`acknowledged`.

Cuando `/ready` o `/metrics` detectan un fallo de conexión o infraestructura,
registran el contexto internamente y devuelven únicamente el cuerpo seguro
`{"status":"unavailable"}`. No exponen host, URL, usuario, SQL, driver, stack
trace ni el texto original de la excepción. Errores de programación o de esquema
no se reclasifican como indisponibilidad de base de datos.

## Consecuencias

### Positivas

- Los orquestadores pueden distinguir entre un proceso vivo y una instancia lista
  para atender tráfico dependiente de la base de datos.
- Un fallo temporal de infraestructura se comunica con `503` sin filtrar detalles
  sensibles a los clientes.
- Prometheus u otras herramientas compatibles pueden consumir métricas sin añadir
  una dependencia adicional ni cargar registros completos en memoria.
- Las métricas expresan la operación actual: sensores activos, lecturas
  persistidas y alertas que todavía requieren atención.

### Negativas

- Los tres conteos se obtienen en una única sentencia SQL y representan el mismo
  snapshot a nivel de sentencia. Pueden cambiar entre scrapes o consultas
  sucesivas, porque son métricas operativas y no un reporte histórico congelado.
- `/ready` y `/metrics` dependen de la base de datos y pueden devolver `503`
  durante una interrupción aunque `/health` siga devolviendo `200`.
- El despliegue y la monitorización deben configurar cada endpoint según su
  propósito, sin tratar liveness como prueba de conectividad.

## Alternativas descartadas

### Un único `/health` que consulte la base de datos

Se descarta porque confunde liveness con readiness. Durante una caída de base de
datos impediría distinguir un proceso HTTP disponible de una instancia que no
puede atender operaciones persistentes.

### Devolver detalles de la excepción al cliente

Se descarta porque puede revelar credenciales, hosts, consultas o información de
la infraestructura y no aporta una acción segura al consumidor de la API.

### Métricas JSON propias

Se descarta porque Prometheus text format permite el consumo directo por
herramientas de observabilidad sin definir un formato de métricas adicional.

### Contar entidades en memoria

Se descarta porque cargar sensores, lecturas o alertas completos escala peor que
usar agregados SQL de solo lectura.
