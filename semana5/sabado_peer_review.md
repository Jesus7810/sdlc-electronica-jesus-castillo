# Semana 5 — Sábado: Peer review humano vs. IA

## Objetivo

Realizar una segunda revisión del código de un compañero utilizando primero una revisión humana basada en la checklist de 10 puntos de peer review y posteriormente una revisión independiente asistida por IA.

El objetivo fue comparar ambos resultados para identificar coincidencias, diferencias y limitaciones, y evaluar cómo puede utilizarse la IA como apoyo dentro de un proceso profesional de code review.

## Revisión humana

Primero revisé el proyecto de mi compañero utilizando la checklist de 10 puntos, sin consultar previamente el resultado de una IA.

Los principales aspectos revisados fueron:

- separación de responsabilidades entre capas;
- contratos y códigos HTTP;
- validaciones con Pydantic y reglas de dominio;
- paginación y filtros;
- manejo de errores;
- persistencia con SQLAlchemy;
- DIP y encapsulación;
- pruebas y calidad general del repositorio.

Entre los hallazgos de la revisión humana estuvieron:

1. El `threshold` permite valores no finitos como `NaN` o infinito, lo que puede producir comportamientos incorrectos al evaluar anomalías.
2. Las consultas de alertas filtran por `sensor_id`, pero no existe un índice específico para ese acceso.
3. `GET /sensors/{sensor_id}/alerts` no distingue entre un sensor inexistente y un sensor válido sin alertas, ya que ambos casos pueden producir una lista vacía.
4. Como pregunta de diseño se señaló que la lectura y su posible alerta se confirman mediante operaciones independientes, por lo que se cuestionó si ambas deberían pertenecer a una misma transacción.

El veredicto de la revisión humana fue:

**Aprobado con cambios.**

## Revisión asistida por IA

Una vez terminada y publicada la revisión humana, se realizó una segunda revisión independiente con Codex utilizando el prompt de code review trabajado durante el Día 3.

Se le solicitó buscar exclusivamente:

- problemas relacionados con SOLID y separación de responsabilidades;
- casos borde;
- riesgos reales de seguridad;
- problemas justificables de rendimiento.

La IA coincidió con preocupaciones identificadas durante la revisión humana en varios aspectos:

- validación insuficiente de `threshold`;
- falta de un índice para las consultas de alertas;
- la frontera transaccional entre la creación de una lectura y su alerta, que durante la revisión humana se había planteado como pregunta de diseño.

Además, señaló aspectos que no habían quedado registrados en la revisión humana, entre ellos:

- falta de paginación en el listado de alertas;
- comportamiento de las claves foráneas al eliminar una lectura que tiene alertas;
- una posible condición de carrera al crear sensores duplicados;
- dificultad para establecer nuevamente `threshold` como `null`;
- una consulta redundante del sensor durante la creación de una lectura.

La IA también señaló como riesgo la ausencia de autenticación en un despliegue público. Este hallazgo no se aceptó automáticamente como defecto, porque su severidad depende de los requisitos y del propósito del sistema. Sin conocer que el producto exige restringir las modificaciones a usuarios autenticados, la observación necesita contexto adicional.

## Comparación

La revisión humana y la revisión asistida por IA no produjeron exactamente los mismos resultados.

La IA fue útil para ampliar rápidamente la búsqueda y relacionar comportamientos entre servicios, repositorios, modelos, migraciones y configuración de base de datos.

La revisión humana, por otro lado, detectó un problema en el contrato de la API que la IA no señaló: un sensor inexistente y un sensor válido sin alertas pueden producir la misma respuesta en `GET /sensors/{sensor_id}/alerts`.

También fue necesario aplicar criterio humano sobre los resultados de la IA. Que la IA clasifique un hallazgo con una determinada severidad no significa que deba aceptarse automáticamente; primero debe comprobarse contra el código, los requisitos y el contexto del producto.

## Tres conclusiones

### 1. La IA amplía una revisión, pero no sustituye el criterio del desarrollador

La revisión asistida por IA encontró varios casos que no identifiqué inicialmente, especialmente problemas que requerían relacionar diferentes archivos y capas. Sin embargo, también produjo observaciones cuya importancia dependía del contexto del producto.

Por ello, aprendí que un hallazgo generado por IA debe tratarse como una hipótesis que necesita ser verificada, no como una decisión técnica definitiva.

### 2. La revisión humana y la revisión con IA pueden detectar problemas diferentes

Hubo coincidencias importantes, como la validación de `threshold`, el índice de alertas y la frontera transaccional entre lectura y alerta. Sin embargo, la revisión humana detectó una inconsistencia en el contrato HTTP que la IA no mencionó, mientras que la IA encontró otros casos relacionados con persistencia, concurrencia y rendimiento.

Esto demuestra que ambas revisiones pueden complementarse y que encontrar más observaciones no significa necesariamente realizar una mejor revisión: también importan la relevancia, el contexto y la validez de cada hallazgo.

### 3. Un buen code review requiere evidencia y decisiones justificadas

El aprendizaje más importante de la actividad fue que revisar código no consiste únicamente en buscar errores o aceptar recomendaciones.

El proceso que considero más adecuado es:

```text
inspeccionar el código
        ↓
identificar un posible problema
        ↓
buscar evidencia
        ↓
entender su impacto
        ↓
proponer una corrección
        ↓
decidir si realmente corresponde al alcance y requisitos
```

La IA puede ayudar especialmente en las etapas de identificación y análisis, pero la responsabilidad de aceptar, rechazar o priorizar una recomendación sigue perteneciendo al desarrollador.

## Reflexión final

La actividad cerró la Semana 5 conectando los aprendizajes de los días anteriores.

El prompting permitió delimitar qué debía revisar la IA. Las herramientas de IA permitieron analizar código con rapidez. El code review mostró que sus recomendaciones deben verificarse. Los ADR reforzaron la importancia de justificar las decisiones técnicas. Finalmente, el desarrollo de una feature y esta comparación entre revisión humana e IA mostraron que utilizar IA profesionalmente no consiste en delegarle el desarrollo, sino en integrarla dentro de un proceso donde existen revisión, pruebas, evidencia y criterio humano.
