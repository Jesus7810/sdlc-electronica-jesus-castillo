# Product Backlog — Sistema de monitoreo IoT

Las prioridades siguen el método MoSCoW:

- **Must:** indispensable para el funcionamiento básico.
- **Should:** importante, pero no imprescindible para la primera versión.
- **Could:** mejora deseable para versiones posteriores.
- **Won't:** queda explícitamente fuera del Sprint actual.

## US-01 — Representar una lectura de sensor

**Como** sistema de monitoreo, **quiero** representar cada lectura con sensor, tipo, valor y fecha, **para** procesarla sin perder su contexto.

- **Prioridad:** Must
- **Story points:** 2

```gherkin
Escenario: Crear una lectura válida
  Dado el sensor "TEMP-01" de tipo "temperature"
  Cuando se recibe el valor 24.5 en una fecha válida
  Entonces se crea una lectura asociada a "TEMP-01" con valor 24.5

Escenario: Rechazar una lectura sin identificador
  Dado un identificador vacío
  Cuando se intenta crear una lectura
  Entonces el sistema informa "sensor_id no puede estar vacío"

Escenario: Evitar que una lectura histórica sea modificada
  Dada una lectura ya creada
  Cuando se intenta cambiar su valor
  Entonces la operación es rechazada
```

## US-02 — Detectar temperatura anómala

**Como** encargado de la bodega, **quiero** identificar temperaturas superiores al límite configurado, **para** actuar antes de que se dañe el inventario.

- **Prioridad:** Must
- **Story points:** 3

```gherkin
Escenario: Detectar temperatura superior al límite
  Dado un límite de temperatura de 35 °C
  Cuando se evalúa una lectura de 35.1 °C
  Entonces la lectura es anómala

Escenario: Aceptar temperatura igual al límite
  Dado un límite de temperatura de 35 °C
  Cuando se evalúa una lectura de 35 °C
  Entonces la lectura es normal
```

## US-03 — Detectar humedad anómala

**Como** encargado de la bodega, **quiero** identificar humedades superiores al límite configurado, **para** prevenir condiciones que afecten los productos.

- **Prioridad:** Must
- **Story points:** 3

```gherkin
Escenario: Detectar humedad superior al límite
  Dado un límite de humedad de 80 %
  Cuando se evalúa una lectura de 80.1 %
  Entonces la lectura es anómala

Escenario: Aceptar humedad igual al límite
  Dado un límite de humedad de 80 %
  Cuando se evalúa una lectura de 80 %
  Entonces la lectura es normal
```

## US-04 — Configurar umbrales

**Como** administrador, **quiero** inyectar los límites de temperatura y humedad, **para** adaptar el monitoreo sin modificar el código.

- **Prioridad:** Must
- **Story points:** 2

```gherkin
Escenario: Utilizar límites personalizados
  Dado un detector configurado con 30 °C y 70 %
  Cuando evalúa una temperatura de 31 °C y una humedad de 71 %
  Entonces ambas lecturas son anómalas

Escenario: Rechazar un límite no finito
  Dado un límite con valor infinito
  Cuando se configura el detector
  Entonces se informa que los umbrales deben ser finitos
```

## US-05 — Administrar el envío de alertas

**Como** encargado de la bodega, **quiero** que las anomalías se envíen mediante una estrategia configurable, **para** cambiar el canal sin alterar el flujo.

- **Prioridad:** Must
- **Story points:** 3

```gherkin
Escenario: Delegar una alerta
  Dada una estrategia de alertas configurada
  Cuando el administrador envía "TEMP-01: 38.0 °C"
  Entonces la estrategia recibe exactamente ese mensaje

Escenario: Cambiar el canal de alertas
  Dada una nueva estrategia compatible
  Cuando se configura el administrador con ella
  Entonces las alertas se envían por el nuevo canal
```

## US-06 — Mostrar alertas en consola

**Como** operador local, **quiero** ver las alertas en consola, **para** reaccionar de inmediato durante la supervisión.

- **Prioridad:** Must
- **Story points:** 1

```gherkin
Escenario: Mostrar una alerta
  Dado el canal de consola
  Cuando se envía "HUM-01: 85.0 %"
  Entonces la consola muestra exactamente "HUM-01: 85.0 %"
```

## US-07 — Conservar alertas en archivo

**Como** encargado de la bodega, **quiero** guardar las alertas en un archivo, **para** disponer de evidencia histórica.

- **Prioridad:** Must
- **Story points:** 2

```gherkin
Escenario: Guardar alertas sin sobrescribir
  Dado un archivo sin alertas
  Cuando se envían dos mensajes consecutivos
  Entonces el archivo conserva ambos en líneas separadas
  Y mantiene el orden en que fueron enviados
```

## US-08 — Simular los sensores de la bodega

**Como** equipo de desarrollo, **quiero** generar lecturas gaussianas de temperatura y humedad, **para** validar el sistema sin hardware físico.

- **Prioridad:** Should
- **Story points:** 5

```gherkin
Escenario: Generar una lectura reproducible
  Dado un simulador con una semilla fija
  Cuando genera lecturas con una distribución configurada
  Entonces repite la misma secuencia al utilizar nuevamente esa semilla

Escenario: Rechazar una desviación inválida
  Dada una desviación estándar igual o menor que cero
  Cuando se configura el simulador
  Entonces se informa que la desviación debe ser positiva
```

## US-09 — Ejecutar un ciclo de monitoreo

**Como** encargado de la bodega, **quiero** procesar los 10 sensores cada 30 segundos, **para** recibir alertas ante cualquier condición anómala.

- **Prioridad:** Should
- **Story points:** 5

```gherkin
Escenario: Procesar una hora simulada
  Dados 10 sensores y 60 ciclos
  Cuando se ejecuta el monitoreo
  Entonces se procesan exactamente 600 lecturas
  Y cada lectura anómala produce una alerta
  Y ninguna lectura normal produce una alerta
```

## US-10 — Consultar el historial de lecturas

**Como** supervisor, **quiero** consultar las lecturas anteriores de cada sensor, **para** analizar la evolución de las condiciones de la bodega.

- **Prioridad:** Could
- **Story points:** 5

```gherkin
Escenario: Consultar lecturas en orden cronológico
  Dado un sensor con tres lecturas registradas
  Cuando se consulta su historial
  Entonces se muestran sus tres lecturas ordenadas por fecha

Escenario: Consultar un sensor sin lecturas
  Dado un sensor registrado sin lecturas
  Cuando se consulta su historial
  Entonces se obtiene una colección vacía
```

## US-11 — Notificar alertas por correo

**Como** supervisor remoto, **quiero** recibir alertas por correo, **para** enterarme de las anomalías aunque no esté frente al sistema.

- **Prioridad:** Won't en este Sprint
- **Story points:** 8

```gherkin
Escenario: Enviar una alerta a un destinatario configurado
  Dado un correo válido y el servicio disponible
  Cuando se detecta una anomalía
  Entonces se envía un correo con el sensor, tipo, valor y fecha

Escenario: Conservar la alerta si falla el correo
  Dado que el servicio de correo no está disponible
  Cuando se intenta notificar una anomalía
  Entonces el fallo queda registrado sin perder la alerta
```