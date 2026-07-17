# AI_LOG.md

## Semana 1 - Día 1

### ObjetivoV
Familiarizarme con Python idiomático para ingenieros que vienen de C/C++.

### Interacción con la IA

Comencé solicitando apoyo para comprender la estructura del ejercicio y el propósito de cada archivo (`sensor_models.py`, `sensor_utils.py` y `main.py`). En lugar de pedir el código completo, fui preguntando el significado de conceptos que no conocía, como `dataclass`, `Enum`, `Protocol` y `self`.

Durante el desarrollo de las funciones, intenté escribir algunas implementaciones por mi cuenta. Por ejemplo, al implementar `round_reading()` propuse utilizar `replace()`, pero inicialmente no comprendía cómo debía utilizarse. Después de la explicación corregí la implementación para indicar explícitamente el atributo que debía modificarse.

También pregunté si era mejor crear una variable intermedia (`number_round`) o escribir toda la expresión directamente en el `return`. La IA me explicó cuándo conviene cada opción y por qué la legibilidad es un criterio importante al escribir código.

Para las funciones `serialize_reading()` e `is_same_sensor()` necesité más orientación, ya que no entendía completamente el objetivo de cada una. Después de la explicación implementé y probé ambas funciones hasta que el programa funcionó correctamente.

### Correcciones realizadas

- Corregí el uso de `replace()` indicando el atributo `value`.
- Cambié el nombre de la variable `round` por `rounded_reading` para no sobrescribir la función incorporada `round()`.
- Ajusté el formato del código siguiendo las recomendaciones de estilo de Python.
- Verifiqué que todas las funciones fueran puras y que no modificaran el objeto original.

### Aprendizajes

- Comprendí la diferencia entre modelar datos y procesarlos.
- Entendí el propósito de `dataclass(frozen=True)` y por qué genera objetos inmutables.
- Aprendí a utilizar `replace()` para crear nuevas instancias modificando únicamente un atributo.
- Comprendí cómo funcionan los `Enum` y los `Protocol`.
- Aprendí a escribir funciones puras con anotaciones de tipos (`type hints`).

### Reflexión

Hoy entendí que el objetivo de la actividad no era únicamente escribir cinco funciones, sino aprender una forma más organizada de estructurar código en Python. La IA me ayudó a comprender los conceptos y a corregir mis errores, pero procuré implementar cada parte después de entender por qué se hacía de esa manera.