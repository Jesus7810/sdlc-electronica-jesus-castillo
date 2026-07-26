# Retrospectiva — Semana 2

## ¿Qué salió bien?

Durante esta semana pude comprender mejor cómo se organiza un proyecto utilizando Scrum. El backlog permitió dividir el sistema de monitoreo en historias de usuario con criterios de aceptación claros, prioridad MoSCoW y story points.

También logré aplicar TDD de forma estricta. Antes de implementar cada comportamiento escribí una prueba, confirmé que fallara por la razón esperada y después desarrollé únicamente el código necesario para hacerla pasar. Los commits separados permiten observar los ciclos RED y GREEN en el historial de Git.

La separación del sistema en componentes también funcionó bien. Cada clase tiene una responsabilidad específica: representar lecturas, detectar anomalías, administrar alertas, simular sensores o coordinar el monitoreo.

Al finalizar, las 28 pruebas fueron aprobadas, la cobertura superó el 80 % y tanto Ruff como mypy terminaron sin errores.

## ¿Qué dificultades se presentaron?

Una de las principales dificultades fue mantener el orden correcto del ciclo TDD. Al principio podía parecer más rápido escribir directamente la implementación, pero hacerlo después de la prueba permitió definir primero el comportamiento esperado.

También se presentaron algunos problemas técnicos. mypy detectó un archivo con dos nombres de módulo diferentes, lo cual se corrigió agregando los archivos `__init__.py` necesarios para definir correctamente los paquetes.

Otra dificultad ocurrió al ejecutar únicamente las pruebas de `SensorSimulator`. Aunque sus cuatro casos pasaron, la ejecución terminó con un error de cobertura porque los demás módulos aparecieron con 0 %. Esto se resolvió ejecutando el conjunto completo de pruebas y entendiendo que la cobertura se estaba calculando de forma global.

## ¿Qué aprendí?

Aprendí que TDD no consiste solamente en escribir pruebas, sino en utilizarlas para dirigir el diseño del código. Una prueba RED debe fallar por la razón que se pretende resolver; después, GREEN busca la implementación mínima y REFACTOR permite mejorar el diseño sin cambiar el comportamiento.

También comprendí mejor la diferencia entre los criterios de aceptación y la Definition of Done. Los criterios describen el comportamiento específico que debe cumplir cada historia, mientras que la Definition of Done establece las condiciones generales de calidad necesarias para considerarla terminada.

Además, reforcé los siguientes conceptos:

- Inyección de dependencias para evitar valores y comportamientos fijos.
- Uso de `Protocol` para depender de contratos.
- Estrategias intercambiables para enviar alertas.
- Inmutabilidad de datos que representan eventos históricos.
- Simulaciones reproducibles mediante semillas.
- Importancia de verificar pruebas, cobertura, estilo y tipos antes de cerrar una historia.

## ¿Qué podría mejorar?

Necesito fortalecer mi capacidad para diseñar las pruebas antes de recibir orientación y anticipar mejor los casos límite de cada historia.

También puedo mejorar la estimación con story points. Todavía debo practicar cómo valorar una historia considerando su complejidad, incertidumbre y esfuerzo relativo, en lugar de pensar solamente en el tiempo necesario.

En la documentación debo continuar buscando un equilibrio entre explicar suficientemente las decisiones y evitar información repetida o innecesaria.

## Acción concreta para la siguiente semana

Antes de implementar cada nueva historia, escribiré por mi cuenta al menos:

1. Un caso exitoso.
2. Un caso inválido o de error.
3. Un caso límite.

Después compararé esos casos con los criterios de aceptación y confirmaré que la prueba RED falle por la razón correcta antes de comenzar la implementación.