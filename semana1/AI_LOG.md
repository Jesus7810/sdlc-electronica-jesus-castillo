### Entradas específicas de uso de IA

#### Entrada 1
- **Consulta:** Cómo dividir el driver UART en responsabilidades.
- **Propuesta de la IA:** Crear clases separadas para configuración, parsers, dispositivo y persistencia.
- **Decisión tomada:** Mantener esa separación porque facilita las pruebas y aplica SRP.
- **Cambio realizado:** Se evitó mezclar la escritura JSON dentro de `UartDevice`.

#### Entrada 2
- **Consulta:** Cómo permitir que el dispositivo utilizara Modbus o NMEA.
- **Propuesta de la IA:** Recibir un `MessageParser` por medio del constructor.
- **Decisión tomada:** Aplicar inyección de dependencias para no crear un parser concreto dentro del dispositivo.
- **Cambio realizado:** `UartDevice` recibe el parser desde el exterior.

#### Entrada 3
- **Consulta:** Cómo simplificar la implementación para mantenerla acorde con el nivel de la semana.
- **Propuesta de la IA:** Utilizar una validación Modbus con checksum.
- **Decisión tomada:** Reemplazarla por un frame educativo más sencillo.
- **Motivo:** El objetivo era practicar SOLID y pruebas unitarias, no implementar el protocolo Modbus completo.

#### Entrada 4
- **Revisión realizada:** Se detectó una importación de `pytest` que no se utilizaba en `test_parsers.py`.
- **Decisión tomada:** Eliminar la importación.
- **Motivo:** Evitar advertencias y mantener el código limpio.