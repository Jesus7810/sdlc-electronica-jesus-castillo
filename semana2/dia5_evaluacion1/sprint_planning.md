# Sprint 1 Planning — Sistema de monitoreo IoT

## Duración del Sprint

Una semana.

## Sprint Goal

Construir y validar el núcleo del sistema de monitoreo de la bodega, capaz de representar lecturas de temperatura y humedad, detectar anomalías mediante umbrales configurables y emitir alertas utilizando diferentes estrategias.

## Historias seleccionadas

| ID | Historia | Prioridad | Story points | Justificación |
|---|---|---:|---:|---|
| US-01 | Representar una lectura de sensor | Must | 2 | Proporciona el modelo de datos utilizado por los demás componentes. |
| US-02 | Detectar temperatura anómala | Must | 3 | Permite identificar temperaturas que podrían dañar el inventario. |
| US-03 | Detectar humedad anómala | Must | 3 | Permite identificar niveles de humedad perjudiciales. |
| US-04 | Configurar umbrales | Must | 2 | Evita límites fijos y permite adaptar el sistema a otras bodegas. |
| US-05 | Administrar el envío de alertas | Must | 3 | Desacopla el flujo de monitoreo del medio de notificación. |
| US-06 | Mostrar alertas en consola | Must | 1 | Proporciona retroalimentación inmediata al operador local. |
| US-07 | Conservar alertas en archivo | Must | 2 | Mantiene evidencia histórica de las anomalías detectadas. |

**Total comprometido:** 16 story points.

## Justificación de la selección

Las siete historias seleccionadas forman el flujo mínimo útil del sistema:

1. Se representa una lectura con todos los datos necesarios.
2. La lectura se evalúa utilizando límites configurables.
3. Si el valor supera el límite correspondiente, se identifica como anomalía.
4. La alerta se delega a una estrategia.
5. La estrategia muestra el mensaje en consola o lo conserva en un archivo.

Las historias US-08 y US-09 se consideran una extensión del Sprint para obtener la Distinción. Se trabajarán únicamente después de completar y validar las historias comprometidas.

US-10 se conserva en el Product Backlog para una versión posterior porque consultar el historial aporta valor, pero no es indispensable para demostrar el flujo principal.

US-11 queda explícitamente fuera de este Sprint debido a su mayor complejidad y a la dependencia de un servicio externo de correo.

## Tareas técnicas

### US-01 — Representar una lectura

- Definir los datos necesarios para una lectura. Tiempo estimado: 30 minutos.
- Escribir pruebas para creación, validaciones e inmutabilidad. Tiempo estimado: 1 hora.
- Implementar `SensorReading` mediante TDD. Tiempo estimado: 1 hora.
- Refactorizar y ejecutar controles de calidad. Tiempo estimado: 30 minutos.

### US-02, US-03 y US-04 — Detectar anomalías

- Definir los casos normales, anómalos y de frontera. Tiempo estimado: 30 minutos.
- Escribir pruebas para temperatura y humedad. Tiempo estimado: 1 hora.
- Probar límites exactos de 35 °C y 80 %. Tiempo estimado: 30 minutos.
- Implementar `AnomalyDetector` con umbrales inyectados. Tiempo estimado: 1 hora.
- Validar umbrales inválidos y tipos no compatibles. Tiempo estimado: 30 minutos.
- Refactorizar y ejecutar controles de calidad. Tiempo estimado: 30 minutos.

### US-05, US-06 y US-07 — Gestionar alertas

- Definir el contrato de las estrategias de alerta. Tiempo estimado: 30 minutos.
- Crear una estrategia falsa para probar la delegación. Tiempo estimado: 30 minutos.
- Escribir las pruebas RED del administrador de alertas. Tiempo estimado: 1 hora.
- Implementar `AlertManager` y la abstracción `AlertStrategy`. Tiempo estimado: 1 hora.
- Escribir pruebas para consola y archivo. Tiempo estimado: 1 hora.
- Implementar `ConsoleAlertStrategy` y `FileAlertStrategy`. Tiempo estimado: 1 hora.
- Verificar que el archivo agregue alertas sin sobrescribirlas. Tiempo estimado: 30 minutos.
- Refactorizar y ejecutar controles de calidad. Tiempo estimado: 30 minutos.

### Integración y cierre

- Ejecutar todas las pruebas y revisar los casos borde. Tiempo estimado: 1 hora.
- Medir y revisar la cobertura. Tiempo estimado: 30 minutos.
- Ejecutar Ruff y mypy. Tiempo estimado: 30 minutos.
- Revisar el historial de commits y el diff. Tiempo estimado: 30 minutos.
- Completar README, retrospectiva y AI_LOG. Tiempo estimado: 1 hora.

Ninguna tarea técnica supera las cuatro horas.

## Definition of Done

Una historia se considera terminada cuando:

- Sus criterios de aceptación están escritos y son verificables.
- Las pruebas se escribieron antes de la implementación.
- Se comprobó el estado RED por la razón esperada.
- Se implementó únicamente el comportamiento necesario para alcanzar GREEN.
- Todas las pruebas relacionadas pasan.
- Se incluyeron casos normales, casos borde y errores relevantes.
- El código tiene nombres claros y type hints.
- Las responsabilidades están separadas.
- Los umbrales se reciben desde fuera y no están hardcodeados.
- `AlertManager` depende de una abstracción.
- La cobertura total es igual o superior al 80 %.
- Ruff no reporta errores.
- mypy no reporta errores.
- Los commits son atómicos y tienen mensajes descriptivos.
- La documentación relacionada está actualizada.
- El diff fue revisado antes de integrar los cambios.

## Riesgos del Sprint

| Riesgo | Medida preventiva |
|---|---|
| Escribir la implementación antes de las pruebas | Respetar un commit RED antes de cada commit GREEN. |
| Confundir `>` con `>=` en los límites | Probar expresamente 35, 35.1, 80 y 80.1. |
| Acoplar las alertas a consola o archivo | Utilizar una abstracción e inyección de dependencias. |
| Obtener cobertura alta con pruebas poco útiles | Probar reglas del dominio, errores y casos frontera. |
| Ampliar demasiado el alcance | Completar primero las siete historias comprometidas. |

## Extensión para Distinción

Después de cumplir la Definition of Done del Sprint se desarrollarán:

- **US-08:** simulación gaussiana reproducible de sensores.
- **US-09:** integración de 10 sensores durante 60 ciclos.
- Un test que compruebe exactamente 600 lecturas.
- Correspondencia entre lecturas anómalas y alertas emitidas.
- Un diagrama C4 nivel 2 de la arquitectura.