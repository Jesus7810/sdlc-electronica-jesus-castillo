# AI_LOG.md

## Semana 1 - Día 3

### Objetivo

Comprender y aplicar los principios SOLID (SRP, OCP y LSP) mediante ejemplos sencillos y pruebas unitarias, con el propósito de desarrollar criterio para diseñar código más mantenible y extensible.

---

### Interacción con la IA

Antes de comenzar a escribir código, trabajé junto con la IA para comprender el propósito de cada principio SOLID. En lugar de enfocarnos únicamente en implementar ejemplos, analizamos qué problema intenta resolver cada principio y por qué es importante en proyectos reales.

Durante el estudio de SRP discutimos cómo identificar cuándo una clase tiene más de una responsabilidad y cómo separar esas responsabilidades en clases independientes.

En OCP analizamos la diferencia entre un diseño que requiere modificar una clase cada vez que aparece un nuevo comportamiento y otro basado en abstracciones, donde es posible extender la funcionalidad sin modificar el código existente. Inicialmente trabajamos con un ejemplo más completo, pero posteriormente decidimos simplificarlo para que el principio fuera más claro y estuviera alineado con el nivel del curso.

En LSP analizamos la importancia de respetar el contrato definido por una clase base. Se revisó por qué una clase derivada debe poder sustituir a la clase padre sin alterar el funcionamiento del programa y cómo identificar un ejemplo que viola este principio.

Una vez comprendidos los conceptos, implementé ejemplos "mal" y "bien" para cada principio, así como dos pruebas unitarias por principio para verificar su comportamiento.

---

### Correcciones realizadas

- Simplifiqué los ejemplos inicialmente propuestos para enfocarlos únicamente en demostrar el principio SOLID correspondiente, eliminando complejidad innecesaria.
- Reorganicé el código para mantener una estructura más clara y fácil de entender.
- Implementé ejemplos separados para los casos que cumplen y los que violan cada principio.
- Añadí pruebas unitarias utilizando `pytest` para validar el comportamiento de cada ejemplo.

---

### Aprendizajes

- Un principio SOLID no busca únicamente que el programa funcione, sino que sea más fácil de mantener y extender.
- SRP establece que una clase debe tener una única responsabilidad.
- OCP promueve diseñar el código para poder agregar nuevas funcionalidades sin modificar las clases existentes.
- LSP indica que una clase derivada debe poder sustituir a su clase base sin romper el comportamiento esperado.
- Las pruebas unitarias también sirven para validar que un diseño se comporta como se espera, además de comprobar que el código funciona correctamente.

---

### Reflexión

Durante esta actividad comprendí que escribir código que funcione no siempre significa escribir buen código. Los principios SOLID proporcionan una guía para diseñar software más organizado, reutilizable y fácil de mantener. También confirmé que ejemplos sencillos permiten comprender mejor el objetivo de cada principio antes de aplicarlos en proyectos de mayor complejidad. Considero que esta actividad fortaleció mi criterio para evaluar la calidad del diseño de una solución, más allá de que simplemente produzca el resultado esperado.