# AI_LOG.md

## Semana 1 - Día 4

### Objetivo

Comprender y aplicar dos principios SOLID fundamentales:

- Interface Segregation Principle (ISP).
- Dependency Inversion Principle (DIP).

El objetivo fue aprender a diseñar software desacoplado mediante interfaces pequeñas y dependencias hacia abstracciones, en lugar de depender de implementaciones concretas.

---

### Interacción con la IA

Durante esta actividad trabajé siguiendo un enfoque de aprendizaje guiado. Antes de escribir código, analicé el propósito de cada principio y razoné por qué existen y qué problemas resuelven.

Para ISP comprendí que una interfaz grande obliga a las clases a implementar métodos que no necesitan, por lo que diseñé protocolos pequeños y específicos (`Readable`, `Writable` y `Calibratable`).

En DIP analicé cómo un componente de alto nivel puede depender de un contrato (`Protocol`) en lugar de una implementación específica. También profundicé en el funcionamiento del constructor, el uso de `self`, la creación de atributos y la inyección de dependencias mediante el repositorio.

Durante la implementación razoné sobre la estructura de datos más adecuada para almacenar las lecturas, comparando el uso de listas y diccionarios antes de implementar `InMemoryRepository`.

Finalmente desarrollé pruebas unitarias para verificar el funcionamiento de las implementaciones y validar que los principios se aplicaran correctamente.

---

### Correcciones realizadas

- Corregí la definición del protocolo `DataRepository` para que `get_latest()` pudiera devolver `None` cuando no existieran lecturas.
- Comprendí la diferencia entre un `Protocol` y una implementación concreta.
- Corregí la implementación inicial de `TemperatureSensor`, incorporando un constructor y un estado interno para la calibración.
- Implementé `InMemoryRepository` utilizando un diccionario para optimizar la búsqueda de la última lectura por sensor.
- Implementé `DataProcessor` aplicando correctamente el principio DIP mediante inyección de dependencias.
- Desarrollé pruebas unitarias para validar sensores, repositorio y procesador.

---

### Aprendizajes

Durante esta actividad comprendí que:

- ISP busca crear interfaces pequeñas y específicas para evitar dependencias innecesarias.
- DIP permite desacoplar la lógica de negocio de los detalles de implementación mediante abstracciones.
- `Protocol` define contratos y no implementaciones.
- La inyección de dependencias permite cambiar implementaciones sin modificar la lógica principal.
- `@dataclass(frozen=True)` es adecuada para representar objetos inmutables que únicamente contienen información.
- Un diccionario resulta más eficiente que una lista cuando el objetivo es recuperar rápidamente la última lectura de un sensor.
- Las pruebas unitarias permiten comprobar que el comportamiento esperado del sistema realmente funciona.

---

### Reflexión

Esta actividad fue una de las más importantes hasta ahora porque me permitió comprender cómo diseñar software desacoplado y mantenible. Más allá de implementar clases y métodos, aprendí a analizar responsabilidades, elegir estructuras de datos según las necesidades del sistema y aplicar principios de diseño que se utilizan en proyectos reales.

También reforcé la importancia de comprender cada línea de código antes de continuar, especialmente conceptos como `Protocol`, la inyección de dependencias y la creación de atributos dentro del constructor.