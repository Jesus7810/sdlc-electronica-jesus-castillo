# Evaluación 1 — Sistema de monitoreo de sensores

## Descripción

Este proyecto implementa una primera versión de un sistema de monitoreo de sensores. El sistema permite representar lecturas, detectar valores anómalos mediante umbrales configurables, enviar alertas usando diferentes estrategias y simular el funcionamiento de varios sensores.

El desarrollo se realizó aplicando Scrum, historias de usuario con criterios de aceptación en Gherkin y ciclos de TDD **Red → Green → Refactor**.

## Funcionalidades implementadas

* Creación de lecturas inmutables de temperatura y humedad.
* Validación de identificadores, valores y fechas.
* Detección de anomalías con umbrales inyectados.
* Envío de alertas mediante estrategias de consola y archivo.
* Simulación gaussiana reproducible mediante semillas.
* Monitoreo integrado de 10 sensores durante 60 ciclos.
* Generación de 600 lecturas y una alerta por cada anomalía detectada.

## Estructura principal

```text
dia5_evaluacion1/
├── tests/
│   ├── test_alert_manager.py
│   ├── test_anomaly_detector.py
│   ├── test_monitoring_integration.py
│   ├── test_sensor_reading.py
│   └── test_sensor_simulator.py
├── alert_manager.py
├── anomaly_detector.py
├── architecture.md
├── monitoring_service.py
├── retrospective.md
├── sensor_reading.py
├── sensor_simulator.py
└── README.md
```

## Historias desarrolladas mediante TDD

| Historias            | Componente          | Comportamiento principal                            |
| -------------------- | ------------------- | --------------------------------------------------- |
| US-01                | `SensorReading`     | Crear y validar lecturas de sensores                |
| US-02, US-03 y US-04 | `AnomalyDetector`   | Detectar anomalías con umbrales configurables       |
| US-05, US-06 y US-07 | `AlertManager`      | Enviar alertas mediante estrategias intercambiables |
| US-08                | `SensorSimulator`   | Generar lecturas gaussianas reproducibles           |
| US-09                | `MonitoringService` | Integrar 10 sensores durante 60 ciclos              |

Cada funcionalidad comenzó con una prueba que fallaba por la razón esperada. Después se agregó la implementación mínima para hacerla pasar y se revisó el código antes de continuar.

El historial de Git conserva commits separados para las etapas RED y GREEN.

## Decisiones de diseño

* `SensorReading` es una `dataclass` inmutable porque una lectura histórica no debería modificarse.
* `AnomalyDetector` recibe los umbrales desde el exterior para evitar valores fijos y facilitar las pruebas.
* `AlertManager` depende del protocolo `AlertStrategy`, no de una implementación concreta.
* Las estrategias de consola y archivo pueden intercambiarse sin modificar el administrador de alertas.
* Cada `SensorSimulator` utiliza su propio generador aleatorio y una semilla para producir resultados reproducibles.
* `MonitoringService` solamente coordina la simulación, detección y generación de alertas.

Estas decisiones aplican principalmente separación de responsabilidades, inversión de dependencias y apertura a nuevas estrategias.

## Ejecución de pruebas

Desde la raíz del repositorio:

```powershell
python -m pytest semana2/dia5_evaluacion1/tests -v
```

El conjunto actual contiene 28 pruebas y comprueba:

* Validaciones de las lecturas.
* Casos normales, anómalos y valores límite.
* Inyección de diferentes umbrales.
* Delegación de alertas.
* Escritura acumulativa en archivos.
* Reproducibilidad de las simulaciones.
* Integración de 10 sensores y 60 ciclos.

## Verificación de calidad

```powershell
python -m pytest semana2/dia5_evaluacion1/tests -v
python -m ruff check semana2/dia5_evaluacion1
python -m mypy semana2/dia5_evaluacion1
```

Resultados obtenidos:

* 28 pruebas aprobadas.
* Cobertura superior al 80 %.
* Ruff sin errores.
* mypy sin errores.

## Definition of Done

Una historia se considera terminada cuando cumple lo siguiente:

* Sus criterios de aceptación son claros y verificables.
* Se escribió primero una prueba que falla por la razón esperada.
* Se implementó únicamente el código necesario para hacer pasar la prueba.
* Se revisó y simplificó el código cuando fue necesario.
* Todas las pruebas relacionadas pasan.
* No se afectan funcionalidades desarrolladas anteriormente.
* Ruff no reporta problemas de estilo.
* mypy no reporta errores de tipos.
* La cobertura total se mantiene en al menos 80 %.
* Los commits RED y GREEN quedan registrados de manera separada y descriptiva.
* La documentación correspondiente está actualizada.

## Documentación complementaria

* El backlog contiene al menos 10 historias priorizadas con MoSCoW, story points y criterios de aceptación en Gherkin.
* `architecture.md` explica la relación entre los componentes.
* `retrospective.md` documenta la retrospectiva del Sprint.
* `AI_LOG.md` registra las decisiones tomadas con apoyo de IA, incluyendo qué propuestas se aceptaron o rechazaron y por qué.
