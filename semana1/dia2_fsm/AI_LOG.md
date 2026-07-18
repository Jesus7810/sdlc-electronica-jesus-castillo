# AI_LOG.md

## Semana 1 - Día 2

### Objetivo

Comprender cómo modelar una Máquina de Estados Finitos (FSM) utilizando programación orientada a objetos y aprender a validar su funcionamiento mediante pruebas unitarias con `pytest`.

### Interacción con la IA

Comencé analizando el archivo `fsm_demo.py` antes de escribir cualquier prueba. En lugar de empezar directamente con el código, pedí que me explicara el propósito de la actividad y el funcionamiento de cada parte de la clase. Revisamos paso a paso el constructor (`__init__`), el uso de `@property`, el método `transition()` y el diccionario de transiciones.

Durante la revisión fui respondiendo con mis propias palabras qué entendía de cada sección. En algunos casos la IA confirmó que mi razonamiento era correcto y, en otros, me corrigió pequeñas confusiones. Por ejemplo, pensaba que `@property` impedía completamente acceder al atributo `_state`, cuando en realidad solo proporciona una interfaz pública más adecuada para consultar el estado.

Al comenzar las pruebas unitarias intenté escribir el segundo test por mi cuenta, pero inicialmente traté de acceder directamente al diccionario de transiciones. Después de analizarlo comprendí que debía utilizar la interfaz pública de la clase y llamar al método `transition()` en lugar de intentar modificar internamente el estado.

También cometí el error de escribir `semaforo.transition` sin paréntesis. En lugar de corregirlo directamente, la IA me hizo reflexionar sobre la diferencia entre hacer referencia a un método y ejecutarlo, comparándolo con funciones como `print` y `print()`. Después de esa explicación comprendí el error y lo corregí.

Para el tercer test propuse utilizar varios `assert` para verificar cada estado del semáforo. Analizamos juntos la responsabilidad de cada prueba y comprendí que una buena prueba unitaria debe verificar un único comportamiento. Con esa explicación decidimos comprobar únicamente que, después de tres transiciones, el semáforo regresaba al estado `RED`.

Al escribir el cuarto test observé que no existía una propiedad pública para consultar `_cycle_count`. Pregunté si debía modificarse la clase para agregarla, pero revisamos el objetivo del ejercicio y concluimos que debía mantenerse exactamente como aparecía en el plan de estudios, por lo que el test accedió directamente al atributo interno.

Finalmente, al ejecutar `pytest`, apareció el mensaje `collected 0 items`. En lugar de asumir que el problema era de las pruebas, revisamos juntos el archivo `fsm_demo.py` y detectamos errores de indentación y un error tipográfico entre `transition` y `transitions`. Después de corregirlos, las cuatro pruebas se ejecutaron correctamente.

### Correcciones realizadas

- Corregí el uso de `transition()` agregando los paréntesis para ejecutar el método.
- Dejé de acceder al diccionario de transiciones desde las pruebas y utilicé la interfaz pública de la clase.
- Comprendí que cada prueba debe validar una única responsabilidad.
- Corregí errores de indentación en `fsm_demo.py`.
- Corregí el nombre de la variable `transitions` utilizado dentro del método `transition()`.
- Verifiqué que las cuatro pruebas pasaran correctamente utilizando `pytest`.

### Aprendizajes

- Comprendí cómo funciona una Máquina de Estados Finitos (FSM).
- Entendí la importancia de encapsular el estado dentro de una clase.
- Aprendí la diferencia entre referenciar un método y ejecutarlo.
- Comprendí la estructura Arrange – Act – Assert para escribir pruebas unitarias.
- Aprendí cómo `pytest` descubre automáticamente los archivos y funciones de prueba.
- Entendí por qué una prueba unitaria debe enfocarse en validar un solo comportamiento.

### Reflexión

Hoy comprendí que escribir pruebas unitarias no consiste únicamente en verificar que el programa funcione, sino en demostrar de forma ordenada que cada comportamiento esperado se cumple. La IA me ayudó principalmente haciéndome razonar antes de darme la respuesta, revisando mis propuestas como si fuera una revisión de código en un entorno profesional. Eso hizo que entendiera mucho mejor el funcionamiento de la FSM y el propósito de las pruebas, en lugar de limitarme a copiar el código.