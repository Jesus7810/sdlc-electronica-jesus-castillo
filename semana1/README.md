# Semana 1 - Reflexión sobre los principios SOLID

Durante esta semana trabajé con Python moderno, máquinas de estados, pruebas
unitarias y los cinco principios SOLID. Las actividades me ayudaron a entender
que escribir software no consiste únicamente en lograr que el código funcione,
sino también en organizarlo para que sea claro, comprobable y fácil de
modificar.

## Responsabilidad única — SRP

El principio de responsabilidad única me permitió comprender que una clase no
debe encargarse de tareas que pertenecen a diferentes partes del sistema.

En el Driver UART, `UartConfig` se encarga de representar y validar la
configuración, los parsers procesan mensajes, `UartDevice` administra el estado
de conexión y `DataRecorder` guarda los resultados.

Separar estas responsabilidades permitió probar cada componente de manera
independiente y evitó crear una sola clase con demasiadas funciones.

## Abierto/cerrado — OCP

El principio abierto/cerrado indica que el sistema debe poder extenderse sin
modificar continuamente el código que ya funciona.

Esto se aplicó mediante `MessageParser`. Si fuera necesario agregar un nuevo
protocolo, podría crearse otra clase que implemente `can_parse()` y `parse()`
sin modificar `UartDevice`, `ModbusParser` o `NMEAParser`.

## Sustitución de Liskov — LSP

Este principio establece que las implementaciones deben poder sustituir a la
abstracción sin romper el comportamiento esperado.

Tanto `ModbusParser` como `NMEAParser` pueden entregarse a `UartDevice` porque
ambos respetan el contrato definido por `MessageParser`. El dispositivo no
necesita conocer los detalles internos de cada protocolo.

## Segregación de interfaces — ISP

El principio de segregación de interfaces busca evitar que una clase tenga que
implementar operaciones que no necesita.

`MessageParser` solamente define dos operaciones: reconocer un mensaje y
procesarlo. No obliga a los parsers a implementar conexión, almacenamiento o
logging, porque esas tareas pertenecen a otras clases.

## Inversión de dependencias — DIP

Este fue uno de los principios que más se reflejó en el ejercicio integrador.

`UartDevice` no crea directamente un `ModbusParser` o un `NMEAParser`. En
cambio, recibe un objeto `MessageParser` mediante el constructor. De esta
manera, el dispositivo depende de una abstracción y puede trabajar con
diferentes protocolos.

Esta decisión también facilita las pruebas porque las dependencias pueden
cambiarse sin modificar la implementación de `UartDevice`.

## Aprendizaje de la semana

Antes de estas actividades relacionaba la programación orientada a objetos
principalmente con clases y herencia. Ahora entiendo que también implica tomar
decisiones sobre responsabilidades, dependencias y facilidad de mantenimiento.

La principal enseñanza fue que aplicar SOLID no significa crear más clases o
hacer el código más complejo. Significa separar el problema de forma razonable
para que cada componente tenga un propósito claro.

Las pruebas unitarias ayudaron a comprobar cada comportamiento de forma
independiente. También permitieron detectar errores sin depender de hardware
UART real.

## Resultados

- 32 pruebas aprobadas.
- 97 % de cobertura.
- Ruff sin errores.
- Más de 8 commits en el historial.
- FSM, ejemplos SOLID y Driver UART incluidos en el repositorio.

## Conclusión

La Semana 1 me ayudó a comenzar la transición entre programar soluciones que
solamente funcionan y diseñar software que también sea mantenible, extensible
y comprobable.

Todavía necesito reforzar algunos conceptos, especialmente abstracciones,
inyección de dependencias y tipado estático, pero ahora puedo identificar cómo
los principios SOLID aparecen en una implementación concreta y no solamente
como definiciones teóricas.