## Entradas específicas de uso de IA

### Entrada 1 — Organización del backlog

- **Consulta:** Cómo dividir el sistema de monitoreo en historias de usuario pequeñas, con criterios de aceptación en Gherkin, prioridad MoSCoW y story points.
- **Propuesta de la IA:** Separar las funcionalidades por responsabilidades, como registro de sensores, creación de lecturas, detección de anomalías, envío de alertas y simulación.
- **Qué acepté:** Acepté dividir el sistema en historias independientes porque cada una representa valor para un usuario y puede desarrollarse y probarse por separado.
- **Qué rechacé o modifiqué:** No conservé todas las descripciones iniciales tal como fueron propuestas. Simplifiqué algunas historias y adapté los nombres de los roles al contexto real del sistema.
- **Por qué:** El backlog debía ser comprensible, mantener un alcance adecuado para la semana y estar escrito con un lenguaje que yo pudiera explicar.
- **Resultado:** Se obtuvo un backlog de al menos 10 historias con prioridad MoSCoW, story points y escenarios en formato Gherkin.

### Entrada 2 — Aplicación del ciclo TDD

- **Consulta:** Cómo implementar `SensorRegistry` y posteriormente los componentes de la evaluación respetando el ciclo RED → GREEN → REFACTOR.
- **Propuesta de la IA:** Escribir primero una prueba de comportamiento, comprobar que fallara por la razón esperada, registrar el commit RED y después crear la implementación mínima.
- **Qué acepté:** Acepté separar las pruebas y la implementación en commits distintos porque permite demostrar que las pruebas dirigieron el desarrollo.
- **Qué rechacé:** Rechacé avanzar directamente al código de producción antes de ejecutar y comprobar la prueba RED.
- **Por qué:** Si la prueba nunca falla, no existe evidencia de que pueda detectar la ausencia o el error del comportamiento que se está desarrollando.
- **Resultado:** El historial de Git conserva evidencia de los ciclos RED y GREEN para varias historias, además de un refactor en `SensorRegistry`.

### Entrada 3 — Diseño de lecturas, anomalías y alertas

- **Consulta:** Cómo separar las responsabilidades de `SensorReading`, `AnomalyDetector` y `AlertManager` sin agregar complejidad innecesaria.
- **Propuesta de la IA:** Utilizar una lectura inmutable, inyectar los umbrales en el detector y definir un protocolo para las estrategias de alerta.
- **Qué acepté:** Acepté la inmutabilidad porque una lectura representa un evento histórico. También acepté la inyección de umbrales y el uso de `AlertStrategy` porque facilitan las pruebas y permiten cambiar la configuración o el medio de envío.
- **Qué rechacé o limité:** No se agregaron bases de datos, servicios web, clases abstractas adicionales ni estrategias externas como correo electrónico.
- **Por qué:** Esas extensiones no eran necesarias para cumplir las historias actuales y habrían aumentado el alcance y la complejidad sin aportar evidencia adicional a la evaluación.
- **Resultado:** Cada componente conserva una responsabilidad clara y las estrategias de consola y archivo pueden intercambiarse sin modificar `AlertManager`.

### Entrada 4 — Simulación, integración y herramientas de calidad

- **Consulta:** Cómo crear una simulación reproducible, integrar 10 sensores durante 60 ciclos y resolver los resultados reportados por cobertura y mypy.
- **Propuesta de la IA:** Usar un generador `random.Random(seed)` por simulador, crear `MonitoringService` para coordinar los componentes y agregar archivos `__init__.py` para definir correctamente los paquetes.
- **Qué acepté:** Acepté usar un generador independiente con semilla porque permite repetir las secuencias durante las pruebas. También acepté que `MonitoringService` solo coordinara la generación, detección y envío de alertas.
- **Qué rechacé:** Cuando las cuatro pruebas del simulador pasaron, rechacé modificar su implementación o agregar pruebas innecesarias solamente porque la ejecución mostró 60 % de cobertura.
- **Por qué:** El reporte indicaba que `SensorSimulator` tenía 100 % de cobertura; el porcentaje global disminuyó porque se había ejecutado únicamente ese archivo de pruebas. La solución correcta era ejecutar la suite completa, no cambiar código que ya cumplía su comportamiento.
- **Resultado:** La integración generó 600 lecturas con 10 sensores durante 60 ciclos. Finalmente pasaron 28 pruebas, la cobertura superó el 80 % y Ruff y mypy terminaron sin errores.