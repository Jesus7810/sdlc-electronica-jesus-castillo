# AI_LOG.md

## Semana 1 - Día 5

### Objetivo

Modernizar un driver UART aplicando Python moderno y los principios SOLID, separando la configuración, el procesamiento de protocolos, el control del dispositivo y la persistencia de datos.

También se buscó que el sistema pudiera probarse sin depender de hardware real y que fuera posible utilizar diferentes protocolos sin modificar la clase principal del dispositivo.

### Interacción con la IA

La actividad se desarrolló mediante una revisión conjunta de los requisitos y de las responsabilidades que debía tener cada componente.

Primero se analizó una propuesta completa para el driver. Al revisarla, identifiqué que contenía más elementos de los necesarios para el nivel trabajado durante la semana. Por esta razón, se decidió simplificar la implementación sin eliminar los requisitos principales de la actividad.

Se discutió qué elementos eran realmente necesarios para demostrar los principios SOLID. Se conservaron la clase de configuración inmutable, la abstracción para los parsers, la inyección de dependencias en `UartDevice` y la separación de la persistencia en `DataRecorder`.

También revisé los archivos de pruebas y detecté que `pytest` estaba importado en `test_parsers.py`, aunque no se utilizaba. La importación fue eliminada para evitar advertencias y mantener el código limpio.

La IA funcionó como apoyo para proponer estructuras y explicar conceptos, mientras que las decisiones finales se tomaron después de revisar si cada elemento era necesario, comprensible y adecuado para la actividad.

### Correcciones realizadas

Se simplificó el parser Modbus para trabajar con frames educativos compuestos por dirección, función y datos. No se implementó el CRC real de Modbus RTU porque el objetivo principal de la actividad era practicar diseño orientado a objetos, SOLID y pruebas unitarias.

Se redujo la cantidad de validaciones y elementos auxiliares de la primera propuesta para evitar agregar complejidad que no aportaba directamente al aprendizaje esperado.

`UartDevice` se diseñó para recibir un objeto `MessageParser` desde su constructor. Esto evita que el dispositivo dependa directamente de `ModbusParser` o `NMEAParser`.

La escritura de archivos se separó en la clase `DataRecorder`, evitando mezclar la comunicación UART con la persistencia de información.

Se utilizó `tmp_path` en las pruebas de `DataRecorder` para crear archivos temporales y evitar generar archivos innecesarios dentro del repositorio.

Durante la revisión del código se eliminó la importación no utilizada de `pytest` en `test_parsers.py`, ya que las pruebas de ese archivo solamente utilizan instrucciones `assert`.

### Aprendizajes

Reforcé el uso de `dataclass` y `frozen=True` para crear objetos de configuración inmutables.

Comprendí que una clase abstracta permite definir el comportamiento que deben respetar diferentes implementaciones. En este caso, `ModbusParser` y `NMEAParser` implementan los métodos `can_parse()` y `parse()`.

Entendí que la inyección de dependencias permite entregar una dependencia desde el exterior, en lugar de crearla dentro de la clase que la utiliza. Gracias a esto, `UartDevice` puede trabajar con diferentes parsers.

También aprendí que JSON Lines guarda un objeto JSON por cada línea del archivo, lo que permite agregar registros sin modificar los datos guardados anteriormente.

La revisión de las importaciones también mostró la importancia de atender las advertencias del editor y eliminar elementos que no se utilizan.

### Reflexión

La modernización del driver permitió transformar un diseño con responsabilidades mezcladas en una estructura compuesta por clases pequeñas y fáciles de probar.

La parte más importante de la actividad no fue hacer el código más complejo, sino encontrar una solución suficientemente clara para cumplir los requisitos sin agregar elementos innecesarios.

Revisar y simplificar la primera propuesta ayudó a comprender que una solución profesional no siempre es la que contiene más clases, validaciones o herramientas, sino la que resuelve el problema de manera clara y mantenible.

También comprendí que revisar el código generado por IA es una parte importante del proceso. La IA puede proponer una solución inicial, pero es responsabilidad del desarrollador detectar complejidad innecesaria, importaciones no utilizadas y decisiones que no correspondan con los objetivos reales del proyecto.
