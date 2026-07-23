## US-01: Registrar un sensor

Como administrador de área,  
quiero dar de alta un sensor asignándole un identificador y un tipo,  
para mantener actualizado el inventario e identificar la función de cada dispositivo.

### Scenario: Registrar un sensor correctamente

Given que no existe un sensor con el identificador "TEMP-01"  
When el administrador registra un sensor con identificador "TEMP-01" y tipo "temperatura"  
Then el sistema muestra un mensaje de confirmación  
And el sensor "TEMP-01" aparece en el inventario con el tipo "temperatura"

### Scenario: Rechazar un identificador duplicado

Given que existe un sensor registrado con el identificador "TEMP-01"  
When el administrador intenta registrar otro sensor con el identificador "TEMP-01"  
Then el sistema muestra el mensaje "El identificador ya está registrado"  
And el campo del identificador se resalta en rojo  
And el nuevo sensor no se agrega al inventario

### Scenario: Rechazar un sensor sin identificador

Given que el formulario para registrar un sensor está disponible  
When el administrador intenta registrar un sensor sin ingresar un identificador  
Then el sistema muestra el mensaje "Necesitas ingresar un identificador"  
And el campo del identificador se resalta en rojo  
And el sensor no se agrega al inventario

**Story points:** 3

**Auditoría de IA:**

- **¿Es verificable?** Sí, se puede comprobar el mensaje y la aparición del sensor en el inventario.
- **¿Es ambigua?** Debe definirse el catálogo de tipos de sensor permitidos.
- **¿Qué casos borde contempla?** Identificador duplicado e identificador vacío.
- **¿Qué caso podría agregarse después?** Intentar registrar un tipo de sensor no permitido.

---

## US-02: Asignar un sensor a una zona

Como administrador de área,  
quiero asignar cada sensor registrado a una zona de monitoreo,  
para conocer su ubicación y organizar los dispositivos instalados.

### Scenario: Asignar un sensor a una zona correctamente

Given que el sensor "TEMP-01" está registrado y la zona "Almacén A" existe  
When el administrador asigna el sensor "TEMP-01" a la zona "Almacén A"  
Then el sistema muestra el mensaje "Sensor asignado correctamente"  
And el inventario muestra el sensor "TEMP-01" en la zona "Almacén A"

### Scenario: Rechazar la asignación a una zona inexistente

Given que el sensor "TEMP-01" está registrado  
And no existe una zona llamada "Almacén Z"  
When el administrador intenta asignar el sensor a la zona "Almacén Z"  
Then el sistema muestra el mensaje "La zona no existe"  
And conserva sin cambios la ubicación actual del sensor

### Scenario: Rechazar la asignación de un sensor inexistente

Given que la zona "Almacén A" existe  
And no existe un sensor con el identificador "TEMP-99"  
When el administrador intenta asignar el sensor "TEMP-99" a la zona "Almacén A"  
Then el sistema muestra el mensaje "El sensor no está registrado"  
And no modifica el inventario

**Story points:** 2

**Auditoría de IA:**

- **¿Es verificable?** Sí, la zona asignada puede comprobarse en el inventario.
- **¿Es ambigua?** Debe aclararse si un sensor puede pertenecer a más de una zona; por ahora se considera una sola.
- **¿Qué casos borde contempla?** Zona inexistente y sensor inexistente.
- **¿Qué caso podría agregarse después?** Reubicar un sensor que ya pertenece a otra zona.

---

## US-03: Registrar una lectura de sensor

Como sistema de monitoreo,  
quiero registrar las lecturas enviadas por cada sensor con su valor y fecha de medición,  
para conservar un historial del comportamiento de la zona monitoreada.

### Scenario: Registrar una lectura correctamente

Given que existe un sensor con el identificador "TEMP-01"  
When el sensor envía una lectura de 24.3 °C con fecha y hora actuales  
Then la lectura se guarda asociada al sensor "TEMP-01"  
And aparece en su historial con el valor y la fecha de medición

### Scenario: Rechazar una lectura de un sensor inexistente

Given que no existe un sensor con el identificador "TEMP-99"  
When se intenta registrar una lectura de 24.3 °C para el sensor "TEMP-99"  
Then el sistema muestra el mensaje "El sensor no está registrado"  
And la lectura no se guarda en el historial

### Scenario: Rechazar una lectura sin valor

Given que existe un sensor con el identificador "TEMP-01"  
When el sensor envía una lectura sin un valor de medición  
Then el sistema muestra el mensaje "La lectura debe contener un valor"  
And la lectura no se guarda en el historial

**Story points:** 3

**Auditoría de IA:**

- **¿Es verificable?** Sí, puede comprobarse la asociación y aparición de la lectura en el historial.
- **¿Es ambigua?** Debe definirse el formato exacto de fecha y hora.
- **¿Qué casos borde contempla?** Sensor inexistente y lectura sin valor.
- **¿Qué caso podría agregarse después?** Rechazar una fecha futura o una unidad incompatible.

---

## US-04: Consultar el historial de lecturas

Como monitor de la zona,  
quiero consultar el historial de lecturas de un sensor,  
para analizar cómo han cambiado las condiciones de la zona durante un periodo determinado.

### Scenario: Consultar el historial de un sensor

Given que el sensor "TEMP-01" tiene lecturas registradas  
When el monitor consulta su historial  
Then el sistema muestra las lecturas asociadas al sensor "TEMP-01"  
And las presenta ordenadas de la más reciente a la más antigua

### Scenario: Consultar un sensor sin lecturas

Given que el sensor "TEMP-02" está registrado pero no tiene lecturas  
When el monitor consulta su historial  
Then el sistema muestra el mensaje "Este sensor todavía no tiene lecturas registradas"  
And no muestra datos pertenecientes a otros sensores

### Scenario: Consultar el historial de un sensor inexistente

Given que no existe un sensor con el identificador "TEMP-99"  
When el monitor intenta consultar su historial  
Then el sistema muestra el mensaje "El sensor no está registrado"  
And no muestra ningún historial

**Story points:** 2

**Auditoría de IA:**

- **¿Es verificable?** Sí, se puede comprobar el contenido, el sensor y el orden de las lecturas.
- **¿Es ambigua?** Falta definir cuántas lecturas se mostrarán cuando el historial sea muy grande.
- **¿Qué casos borde contempla?** Sensor sin lecturas y sensor inexistente.
- **¿Qué caso podría agregarse después?** Filtrar por un intervalo de fechas.

---

## US-05: Detectar lecturas anómalas

Como monitor de la zona,  
quiero que el sistema identifique automáticamente las lecturas que superen los límites configurados,  
para detectar condiciones anormales que requieran atención.

### Scenario: Detectar una temperatura anómala

Given que el límite máximo de temperatura está configurado en 35 °C  
When el sensor "TEMP-01" registra una lectura de 38 °C  
Then el sistema clasifica la lectura con el estado "ANÓMALA"  
And conserva la lectura en el historial del sensor

### Scenario: Aceptar una temperatura dentro del límite

Given que el límite máximo de temperatura está configurado en 35 °C  
When el sensor "TEMP-01" registra una lectura de 30 °C  
Then el sistema clasifica la lectura con el estado "NORMAL"  
And no genera una anomalía

### Scenario: Evaluar una lectura en el valor límite

Given que el límite máximo de temperatura está configurado en 35 °C  
When el sensor "TEMP-01" registra una lectura de 35 °C  
Then el sistema clasifica la lectura con el estado "NORMAL"  
And no genera una anomalía

**Story points:** 3

**Auditoría de IA:**

- **¿Es verificable?** Sí, los valores, el umbral y los estados esperados están definidos.
- **¿Es ambigua?** No, siempre que la regla sea que solo los valores mayores al límite son anómalos.
- **¿Qué caso borde contempla?** Una lectura exactamente igual al límite.
- **¿Qué caso podría agregarse después?** Aplicar límites diferentes según el tipo de sensor.

---

## US-06: Configurar los límites de anomalía

Como administrador de área,  
quiero configurar los límites permitidos para cada tipo de medición,  
para adaptar la detección de anomalías a las condiciones de la zona monitoreada.

### Scenario: Configurar un límite de temperatura

Given que el tipo de sensor "temperatura" está registrado  
When el administrador establece un límite máximo de 35 °C  
Then el sistema guarda el límite de 35 °C para los sensores de temperatura  
And utiliza ese valor para evaluar las nuevas lecturas

### Scenario: Rechazar un límite sin valor numérico

Given que está disponible la configuración de límites  
When el administrador ingresa "alto" como límite máximo de temperatura  
Then el sistema muestra el mensaje "El límite debe ser un valor numérico"  
And conserva la configuración anterior

### Scenario: Rechazar límites inconsistentes

Given que el límite mínimo de humedad está configurado en 30 %  
When el administrador intenta establecer un límite máximo de 20 %  
Then el sistema muestra el mensaje "El límite máximo debe ser mayor que el mínimo"  
And no guarda la nueva configuración

**Story points:** 3

**Auditoría de IA:**

- **¿Es verificable?** Sí, puede comprobarse el valor guardado y su uso en lecturas posteriores.
- **¿Es ambigua?** Debe definirse si los límites se configuran por tipo, zona o sensor; aquí se configuran por tipo.
- **¿Qué casos borde contempla?** Valor no numérico y límites inconsistentes.
- **¿Qué caso podría agregarse después?** Configurar un límite específico para un solo sensor.

---

## US-07: Generar una alerta por anomalía

Como monitor de la zona,  
quiero recibir una alerta cuando se detecte una lectura anómala,  
para identificar rápidamente el sensor afectado y tomar las medidas necesarias.

### Scenario: Generar una alerta por temperatura elevada

Given que el sensor "TEMP-01" está instalado en la zona "Almacén A"  
And una lectura de 38 °C ha sido clasificada como "ANÓMALA"  
When el sistema procesa la anomalía  
Then genera una alerta con el identificador "TEMP-01"  
And la alerta muestra la zona "Almacén A" y el valor de 38 °C  
And registra la fecha y hora de la anomalía

### Scenario: No generar una alerta para una lectura normal

Given que una lectura de 30 °C del sensor "TEMP-01" está clasificada como "NORMAL"  
When el sistema procesa la lectura  
Then no genera ninguna alerta para esa lectura

### Scenario: Evitar una alerta incompleta

Given que una lectura anómala no está asociada con un sensor registrado  
When el sistema intenta generar la alerta  
Then registra el mensaje "No se pudo identificar el sensor de la anomalía"  
And no envía una alerta incompleta al monitor

**Story points:** 3

**Auditoría de IA:**

- **¿Es verificable?** Sí, puede comprobarse la generación y el contenido de la alerta.
- **¿Es ambigua?** Debe definirse el medio por el cual se entregará la alerta.
- **¿Qué caso borde contempla?** Una anomalía sin sensor válido asociado.
- **¿Qué caso podría agregarse después?** Evitar alertas repetidas por lecturas anómalas consecutivas.

---

## US-08: Seleccionar el medio de alerta

Como administrador de área,  
quiero seleccionar el medio utilizado para emitir las alertas,  
para adaptar las notificaciones a los recursos disponibles en la instalación.

### Scenario: Emitir una alerta en consola

Given que el medio de alerta seleccionado es "consola"  
And se detecta una lectura anómala en el sensor "TEMP-01"  
When el sistema genera la alerta  
Then muestra la alerta en la consola  
And incluye el identificador, la zona, el valor y la fecha de medición

### Scenario: Guardar una alerta en un archivo

Given que el medio de alerta seleccionado es "archivo"  
And se detecta una lectura anómala en el sensor "HUM-01"  
When el sistema genera la alerta  
Then agrega la alerta al archivo de registro  
And conserva las alertas previamente guardadas

### Scenario: Rechazar un medio de alerta no disponible

Given que los medios disponibles son "consola" y "archivo"  
When el administrador intenta seleccionar el medio "SMS"  
Then el sistema muestra el mensaje "El medio de alerta no está disponible"  
And conserva el medio configurado anteriormente

**Story points:** 5

**Auditoría de IA:**

- **¿Es verificable?** Sí, se puede revisar el destino y contenido de cada alerta.
- **¿Es ambigua?** Debe definirse la estructura del archivo; no afecta el comportamiento principal de la historia.
- **¿Qué caso borde contempla?** Seleccionar un medio no disponible y conservar la configuración anterior.
- **¿Qué caso podría agregarse después?** Falla de escritura en el archivo de alertas.

---

## US-09: Consultar el estado de los sensores

Como administrador de área,  
quiero consultar si cada sensor está activo o sin comunicación,  
para detectar dispositivos que requieran revisión o mantenimiento.

### Scenario: Mostrar un sensor activo

Given que el sensor "TEMP-01" envió una lectura hace menos de 60 segundos  
When el administrador consulta el inventario  
Then el sistema muestra el sensor "TEMP-01" con el estado "ACTIVO"  
And muestra la fecha y hora de su última lectura

### Scenario: Detectar un sensor sin comunicación

Given que el sensor "TEMP-02" no ha enviado lecturas durante más de 60 segundos  
When el administrador consulta el inventario  
Then el sistema muestra el sensor "TEMP-02" con el estado "SIN COMUNICACIÓN"  
And muestra la fecha y hora de la última lectura recibida

### Scenario: Mostrar un sensor que nunca ha enviado lecturas

Given que el sensor "TEMP-03" está registrado pero nunca ha enviado una lectura  
When el administrador consulta el inventario  
Then el sistema muestra el sensor "TEMP-03" con el estado "SIN DATOS"  
And no inventa una fecha de última lectura

**Story points:** 3

**Auditoría de IA:**

- **¿Es verificable?** Sí, los estados se determinan a partir del tiempo de la última lectura.
- **¿Es ambigua?** El periodo de 60 segundos debe ser configurable si cambia la frecuencia esperada.
- **¿Qué caso borde contempla?** Un sensor registrado que nunca ha enviado datos.
- **¿Qué caso podría agregarse después?** Recuperación del estado activo después de restablecer la comunicación.

---

## US-10: Consultar un resumen de la zona

Como monitor de la zona,  
quiero consultar un resumen de las lecturas y alertas recientes,  
para conocer rápidamente el estado general de la zona monitoreada.

### Scenario: Mostrar el resumen de una zona

Given que la zona "Almacén A" tiene sensores con lecturas registradas  
When el monitor consulta el resumen de la zona "Almacén A"  
Then el sistema muestra la lectura más reciente de cada sensor de esa zona  
And muestra la cantidad de sensores activos y sin comunicación  
And muestra las alertas activas de la zona

### Scenario: Consultar una zona sin sensores

Given que la zona "Almacén B" existe pero no tiene sensores asignados  
When el monitor consulta su resumen  
Then el sistema muestra el mensaje "La zona no tiene sensores asignados"  
And no muestra datos pertenecientes a otras zonas

### Scenario: Consultar una zona inexistente

Given que no existe una zona llamada "Almacén Z"  
When el monitor intenta consultar su resumen  
Then el sistema muestra el mensaje "La zona no existe"  
And no muestra información de monitoreo

**Story points:** 5

**Auditoría de IA:**

- **¿Es verificable?** Sí, puede comprobarse que el resumen contiene únicamente datos de la zona seleccionada.
- **¿Es ambigua?** Debe definirse qué significa que una alerta permanezca activa.
- **¿Qué casos borde contempla?** Zona sin sensores y zona inexistente.
- **¿Qué caso podría agregarse después?** Actualizar el resumen automáticamente cuando llegue una lectura nueva.

---

**Total estimado:** 32 story points.
