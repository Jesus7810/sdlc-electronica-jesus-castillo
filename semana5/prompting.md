# Semana 5 — Prompting efectivo

## Objetivo

Comparar el resultado de prompts pobres y prompts bien estructurados aplicados a tareas reales de SensorHub.

---

## Tarea 1 — Comprensión del proyecto

### Prompt pobre
Revisa el código de SensorHub y explícame qué entiendes de él.

### Resultado del prompt pobre
SensorHub es una API REST para registrar sensores y sus mediciones, no un sistema de alertas o simulación en su estado actual.
Su flujo principal es:
HTTP/FastAPI → routers → servicios (reglas de negocio) → repositorios → SQLite/PostgreSQL
Lo que hace:
Gestiona sensores: crear, consultar, listar, editar y eliminar.
Cada sensor tiene ID, tipo, unidad y rango operativo.
Sólo admite inicialmente:temperature en C
humidity en %

Registra lecturas asociadas a un sensor existente.
Verifica que la unidad coincida y que el valor esté dentro de min_value y max_value.
Evita lecturas duplicadas para el mismo sensor y mismo timestamp.
Permite filtrar y paginar lecturas, además de editarlas o borrarlas.
Al borrar un sensor, sus lecturas se eliminan en cascada.
La estructura está bien separada:
[routers.py](C:\\Users\\ironm\\OneDrive\\Documentos\\EDSIA\\sdlc-electronica-jesus-castillo\\app\\routers.py): API HTTP, dependencias y conversión de errores a códigos 400/404/409.
[services.py](C:\\Users\\ironm\\OneDrive\\Documentos\\EDSIA\\sdlc-electronica-jesus-castillo\\app\\services.py): reglas de negocio.
[repositories.py](C:\\Users\\ironm\\OneDrive\\Documentos\\EDSIA\\sdlc-electronica-jesus-castillo\\app\\repositories.py): acceso a datos mediante SQLAlchemy.
[models.py](C:\\Users\\ironm\\OneDrive\\Documentos\\EDSIA\\sdlc-electronica-jesus-castillo\\app\\models.py): tablas sensors y readings.
[schemas.py](C:\\Users\\ironm\\OneDrive\\Documentos\\EDSIA\\sdlc-electronica-jesus-castillo\\app\\schemas.py): validación de entradas y salidas con Pydantic.
También conserva /readings como ruta antigua por compatibilidad, aunque la ruta más coherente es /sensors/{sensor_id}/readings.
Hay pruebas unitarias e integrales bastante completas. Al ejecutarlas, 91 pasaron; una no llegó a ejecutarse porque Pytest no pudo crear un directorio temporal por permisos de Windows (PermissionError), no por un fallo funcional de SensorHub. La cobertura reportada fue ~95%.
Un detalle conceptual a mejorar: la regla de “cero absoluto” se aplica antes de comprobar el tipo de sensor; en la práctica el rango operativo bloquea humedades negativas, pero ese mensaje físico debería pertenecer sólo a sensores de temperatura.

### Prompt bueno
CONTEXTO:
Este repositorio contiene actividades históricas de varias semanas además
del proyecto actual SensorHub.

Para este análisis, considera como parte del sistema SensorHub principalmente:
- app/
- tests/
- migrations/
- .github/
- alembic.ini
- Dockerfile
- docker-compose.yml
- render.yaml
- requirements.txt
- pyproject.toml
- README.md
- .env.example

No inspecciones ni utilices .env.
No es necesario inspeccionar sensorhub.db.
No asumas que existe una carpeta llamada "SensorHub".

Las carpetas semana0/, semana1/ y semana2/ contienen ejercicios históricos
y no deben utilizarse para determinar la arquitectura actual de SensorHub.

SensorHub es un proyecto backend desarrollado en Python 3.12 para gestionar
sensores y sus lecturas.

TAREA:
Analiza el código y la configuración indicados y explícame cómo funciona
SensorHub actualmente.

RESTRICCIONES:
- Identifica el propósito general del sistema.
- Explica cómo cumple ese propósito.
- Explica el flujo de una petición desde la API hasta la persistencia.
- Identifica el framework utilizado para construir la API y los métodos HTTP
  relevantes que encuentres.
- Identifica todos los sistemas de base de datos que puede utilizar y explica
  en qué contexto se utiliza cada uno.
- Explica cómo se configura la conexión a la base de datos.
- Identifica la arquitectura por capas y la responsabilidad de cada capa.
- Distingue entre código actual de SensorHub y ejercicios históricos del repositorio.
- Basa cada conclusión únicamente en evidencia disponible en los archivos.
- Si algo no puede determinarse con certeza, indícalo en lugar de asumirlo.

ENTREGA:
Una explicación estructurada dirigida a un desarrollador que acaba de
incorporarse al proyecto. Incluye referencias a los archivos que sustentan
las conclusiones importantes.

### Resultado del prompt bueno
Qué es SensorHub
SensorHub es una API REST en Python para administrar sensores y sus lecturas: permite crear, consultar, modificar y eliminar sensores, y registrar, consultar, actualizar y eliminar mediciones. La aplicación se inicia como una instancia de FastAPI en [app/main.py (line 5)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/main.py:5), y la descripción coincide con el README ([README.md (line 7)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/README.md:7)).
Los tipos soportados por el código actual son exclusivamente:
temperature, cuya unidad válida es C
humidity, cuya unidad válida es %
Esto está definido en [app/domain.py (line 3)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/domain.py:3).
API y operaciones disponibles
El framework es FastAPI; usa rutas declaradas mediante router.get, router.post, @router.patch y @router.delete en [app/routers.py (line 77)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/routers.py:77).
Método	Ruta	Función
GET	/health	Estado simple de la API
POST / GET	/sensors	Crear y listar sensores
GET / PATCH / DELETE	/sensors/{sensor_id}	Consultar, actualizar parcialmente o eliminar un sensor
POST / GET	/sensors/{sensor_id}/readings	Ruta canónica para crear y listar lecturas del sensor
POST / GET	/readings	Rutas antiguas mantenidas por compatibilidad
GET / PATCH / DELETE	/readings/{reading_id}	Consultar, actualizar parcialmente o eliminar una lectura


La ruta canónica de creación obtiene el sensor_id de la URL. Las rutas /readings se llaman explícitamente “legacy” en el código ([app/routers.py (line 188)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/routers.py:188)).
FastAPI y Pydantic validan formato, tipos y límites básicos de entrada mediante los esquemas de [app/schemas.py (line 9)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/schemas.py:9). Por ejemplo, los límites de paginación se validan en la ruta: limit de 1 a 100 y offset no negativo ([app/routers.py (line 204)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/routers.py:204)).
Flujo: de una petición a la persistencia
Para POST /sensors/{sensor_id}/readings el recorrido es:
Cliente HTTP
  → Router FastAPI + esquema Pydantic
  → Inyección de sesión y repositorios
  → ReadingService (reglas de negocio)
  → SqlAlchemyReadingRepository
  → SQLAlchemy Session / commit
  → SQLite o PostgreSQL
FastAPI valida el cuerpo como SensorReadingCreate y resuelve las dependencias del endpoint ([app/routers.py (line 175)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/routers.py:175)).
La dependencia get_db abre una Session; el router construye repositorios SQLAlchemy y el servicio correspondiente ([app/routers.py (line 39)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/routers.py:39), [app/database.py (line 47)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/database.py:47)).
ReadingService.record verifica que exista el sensor, que la unidad coincida, que el valor esté dentro del rango configurado y que no sea menor que -273.15; además evita duplicar el par (sensor_id, timestamp) ([app/services.py (line 177)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/services.py:177)).
El repositorio crea ReadingModel, hace add, commit y refresh ([app/repositories.py (line 55)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/repositories.py:55)).
El router traduce errores de negocio a HTTP: principalmente 400, 404 o 409; FastAPI devuelve 422 para errores de formato previos al servicio ([app/routers.py (line 152)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/routers.py:152)).
Las entidades persistidas son sensors y readings. Una lectura pertenece a un sensor, tiene unicidad por sensor y marca de tiempo, y la FK usa ON DELETE CASCADE ([app/models.py (line 25)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/models.py:25)).
Arquitectura por capas
Presentación/API — main.py, routers.py, schemas.py: expone HTTP, valida contratos de entrada/salida y traduce excepciones a respuestas HTTP.
Dominio — domain.py: concentra las reglas invariables: unidades compatibles y min_value < max_value.
Aplicación/servicios — services.py: implementa los casos de uso y reglas que dependen del estado: existencia, rango operativo, duplicados y restricciones de actualización.
Abstracción de persistencia — protocolos SensorRepository y ReadingRepository: los servicios dependen de contratos, no directamente de SQLAlchemy ([app/services.py (line 16)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/services.py:16)).
Infraestructura/persistencia — repositories.py, models.py, database.py: implementa dichos contratos con SQLAlchemy, define tablas y administra sesiones.
Evolución de esquema — migrations/: Alembic materializa las tablas, índices y restricciones ([migración inicial (line 20)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/migrations/versions/93b8da0ac204_esquema_inicial_sensors_y_readings.py:20)).
Las pruebas aprovechan esta separación: usan repositorios falsos para pruebas unitarias de servicio ([tests/test_services.py (line 9)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/tests/test_services.py:9)) y sustituyen la dependencia de base de datos por SQLite en memoria en las pruebas de API ([tests/test_main.py (line 14)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/tests/test_main.py:14)).
Bases de datos y configuración
El sistema puede usar dos motores:
SQLite: es el valor predeterminado si DATABASE_URL no está definida: sqlite:///sensorhub.db ([app/database.py (line 10)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/database.py:10)). Las pruebas usan una variante SQLite en memoria, no el archivo local.
PostgreSQL: se usa con Docker Compose, que levanta postgres:16 y construye la URL para la API ([docker-compose.yml (line 1)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/docker-compose.yml:1)). Render define una base PostgreSQL administrada e inyecta su cadena como DATABASE_URL ([render.yaml (line 7)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/render.yaml:7)).
La configuración central procede de DATABASE_URL. El código normaliza URL de PostgreSQL convencionales (postgres:// y postgresql://) al dialecto postgresql+psycopg:// ([app/database.py (line 12)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/database.py:12)); psycopg[binary] está entre las dependencias ([requirements.txt (line 11)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/requirements.txt:11)).
Para SQLite, cada conexión habilita PRAGMA foreign_keys=ON, necesario para aplicar la integridad referencial y el borrado en cascada ([app/database.py (line 26)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/database.py:26)).
Alembic toma la misma URL que la aplicación, no el valor de ejemplo de alembic.ini ([migrations/env.py (line 7)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/migrations/env.py:7)). El contenedor ejecuta alembic upgrade head antes de Uvicorn ([Dockerfile (line 13)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/Dockerfile:13)). En ejecución directa con Uvicorn, el código no aplica migraciones automáticamente; deben ejecutarse aparte.
Alcance actual frente a ejercicios históricos
Para este análisis tomé como sistema actual únicamente app/, tests/, migrations/, .github/ y los archivos de configuración indicados. No abrí .env, no inspeccioné sensorhub.db y no utilicé semana0/, semana1/ ni semana2/ para inferir la arquitectura.
Hay una salvedad de configuración: pyproject.toml aún incluye semana2 en testpaths y cobertura ([pyproject.toml (line 7)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/pyproject.toml:7)). Eso significa que pytest y la CI podrían ejecutar también pruebas históricas, pero no cambia la arquitectura actual: la CI analiza app con mypy y ejecuta el conjunto de pruebas configurado ([.github/workflows/ci.yml (line 24)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/.github/workflows/ci.yml:24)).
No encontré evidencia de autenticación, autorización, alertas, simulación de sensores ni procesamiento asíncrono; por tanto, no deben asumirse como funciones actuales.

### Comparación y veredicto
El prompt pobre cumplió con el objetivo general, ya que logró identificar correctamente el funcionamiento y la estructura de SensorHub. Sin embargo, al no establecer un alcance claro, el modelo realizó acciones no solicitadas, como ejecutar pruebas y explorar aspectos adicionales del proyecto. En cambio, el prompt bueno delimitó claramente el contexto, la tarea y las restricciones, por lo que la respuesta se concentró en analizar el funcionamiento y la arquitectura con mayor profundidad y evidencia concreta. Concluyo que un buen prompt no necesariamente hace que una IA sea capaz de responder algo que antes no podía, sino que permite controlar mejor el alcance y obtener un resultado más preciso, predecible y alineado con el objetivo.
---

## Tarea 2 — Revisión arquitectónica

### Prompt pobre
Revisa la arquitectura de SensorHub y dime cómo hacer el código más eficiente.

### Resultado del prompt pobre
La arquitectura por capas es sólida y fácil de evolucionar: router → servicio → repositorio → SQLAlchemy. También evita el N+1 en las rutas actuales. El mayor margen de eficiencia está en reducir viajes a la base de datos y preparar la consulta de telemetría para historiales grandes.
Prioridades:
Elimina comprobaciones duplicadas antes de INSERT.
Crear sensor hace SELECT previo + INSERT.
Registrar lectura hace búsqueda de sensor + consulta de duplicado + INSERT.
Las restricciones de clave primaria y UNIQUE(sensor_id, timestamp) ya garantizan integridad. Inserta directamente y traduce el IntegrityError a un error de dominio. Reduce una consulta por escritura y mantiene seguridad ante concurrencia. Ver [services.py (line 47)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/services.py:47) y [models.py (line 26)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/models.py:26).

Reduce lecturas redundantes al actualizar.
PATCH /readings/{id} consulta la lectura, consulta su sensor para validar y el repositorio vuelve a consultar la lectura antes de actualizar. Haz que el repositorio reciba la entidad ya cargada, o centraliza la transacción en un Unit of Work. Ver [services.py (line 240)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/services.py:240) y [repositories.py (line 119)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/repositories.py:119).

Optimiza la actualización de rango del sensor.
Actualmente, aun si solo cambia name, con lecturas existentes se hacen consultas extra para verificar historial. Ejecuta esa validación únicamente si cambian min_value o max_value; y reemplaza has_for_sensor + all_within_range por una sola consulta agregada (MIN(value), MAX(value)). Ver [services.py (line 86)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/services.py:86).

Cambia la paginación de lecturas a cursor para producción.
OFFSET se vuelve lento conforme crece el desplazamiento. Para telemetría conviene ordenar por timestamp DESC y paginar con before_timestamp (keyset pagination). La restricción única actual (sensor_id, timestamp) ya ayuda a ese patrón; si el producto exige orden por id, define los índices a partir de ese requisito y confírmalo con EXPLAIN ANALYZE. La consulta hoy ordena por id, lo que no aprovecha tan bien los filtros temporales. Ver [repositories.py (line 90)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/repositories.py:90).

Introduce inserción por lotes para sensores que reportan frecuentemente.
Un endpoint de lote, validación agrupada y una única transacción permite insertar decenas o cientos de lecturas con mucha menos latencia que commit() por lectura. Para una siguiente escala, separa la ingesta del CRUD administrativo mediante una cola y un consumidor de persistencia.

Define el límite de transacción fuera del repositorio.
Cada método del repositorio hace commit() por su cuenta. Funciona para CRUD, pero limita operaciones atómicas y batch. Que el servicio/Unit of Work controle commit permite agrupar cambios y hace más sencilla la evolución a procesos de ingesta.

Operación y despliegue.
Configura el pool de PostgreSQL de forma explícita y alinéalo con el número de workers.
No ejecutes Alembic dentro de cada arranque de Uvicorn cuando haya varias réplicas; ejecútalo como paso de despliegue.
Mantén la API síncrona por ahora: migrar a async solo compensa si las métricas muestran saturación por I/O.
Añade métricas de p95, consultas por endpoint y agotamiento del pool antes de introducir caché o particiones.

A nivel de diseño, mover la traducción de IntegrityError fuera de los servicios también desacoplaría el dominio de SQLAlchemy. Hoy la capa de servicio conoce esa excepción de infraestructura. Ver [services.py (line 57)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/services.py:57).
Verificación: las 62 pruebas de SensorHub pasan; Ruff y mypy también. La ejecución global tuvo un único error ajeno a SensorHub, causado por permisos del directorio temporal en semana2/dia5_evaluacion1. No modifiqué archivos.

### Prompt bueno
CONTEXTO:
SensorHub es una API REST desarrollada en Python 3.12 con FastAPI,
SQLAlchemy 2.x y persistencia mediante SQLite o PostgreSQL.

El proyecto utiliza una arquitectura por capas con componentes de API,
dominio, servicios y persistencia.

TAREA:
Realiza una revisión arquitectónica del código actual de SensorHub para
evaluar si las responsabilidades están correctamente separadas y si existen
problemas reales de diseño que afecten su claridad, mantenibilidad o
capacidad de evolución.

RESTRICCIONES:
- Evalúa si cada capa contiene responsabilidades apropiadas.
- Identifica lógica ubicada en una capa que debería pertenecer a otra.
- Detecta acoplamiento innecesario, duplicación o responsabilidades mezcladas.
- No optimices rendimiento salvo que exista evidencia concreta de un problema actual.
- No propongas cambios únicamente por aplicar patrones de diseño.
- No introduzcas microservicios, asincronía, caché, colas u otras piezas de
  infraestructura sin demostrar primero que el proyecto actual las necesita.
- Distingue claramente entre problemas reales, mejoras opcionales y
  optimizaciones prematuras.
- Justifica cada hallazgo con evidencia concreta del repositorio.
- Si la arquitectura actual es adecuada para el tamaño y necesidades del
  proyecto, indícalo explícitamente.
- No modifiques ningún archivo.
- No ejecutes cambios ni refactorizaciones.

ENTREGA:
Para cada hallazgo indica:
1. Archivo o ubicación.
2. Responsabilidad actual.
3. Problema identificado.
4. Por qué importa.
5. Cambio recomendado.
6. Prioridad: alta, media o baja.

Finaliza con un veredicto general sobre si la arquitectura actual necesita
una refactorización importante, ajustes puntuales o ningún cambio.

### Resultado del prompt bueno
La arquitectura actual es adecuada para el tamaño y alcance de SensorHub: los routers manejan HTTP, los servicios coordinan casos de uso y los repositorios concentran SQLAlchemy. No hay evidencia que justifique microservicios, asincronía, caché, colas ni una refactorización grande.
Hallazgos reales
Acoplamiento de servicios a SQLAlchemy y a modelos de persistencia — prioridad mediaUbicación: [app/services.py (line 4)](C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/services.py:4), [app/services.py (line 13)](C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/services.py:13), [app/models.py (line 9)](C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/models.py:9).
Responsabilidad actual: los servicios definen sus protocolos, construyen/devuelven SensorModel y ReadingModel, y convierten IntegrityError de SQLAlchemy en errores de aplicación.
Problema: la capa de aplicación conoce el ORM y una excepción de infraestructura. También los contratos de repositorio exponen directamente los modelos SQLAlchemy. Esto contradice la promesa documentada de poder cambiar almacenamiento sin cambiar reglas de negocio.
Por qué importa: sustituir SQLAlchemy o persistir desde otra fuente obligaría a cambiar services.py y sus pruebas, no solamente la implementación de repositorios. [tests/test_services.py (line 5)](C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/tests/test_services.py:5) confirma ese acoplamiento al usar los modelos ORM en los falsos repositorios.
Cambio recomendado: como ajuste gradual, hacer que los repositorios traduzcan errores de persistencia a errores neutrales y que los servicios dependan de entidades/DTO internos simples. No es necesario hacerlo antes de que exista una segunda implementación de persistencia.

La semántica de “sensor debe existir” para listar lecturas anidadas está en el router — prioridad mediaUbicación: [app/routers.py (line 204)](C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/routers.py:204).
Responsabilidad actual: el endpoint llama primero a service.require_sensor(sensor_id) y después a service.list(...).
Problema: una regla del caso de uso —una colección hija bajo /sensors/{id} requiere que el padre exista— queda repartida entre el adaptador HTTP y el servicio. El método ReadingService.list no la aplica.
Por qué importa: otro adaptador futuro, o una reutilización directa del servicio, puede listar lecturas de un sensor inexistente sin recibir el mismo comportamiento. La ruta anidada devuelve 404, mientras la ruta histórica /readings?sensor_id=... delega directamente a list y devuelve una lista vacía.
Cambio recomendado: exponer un caso de uso explícito, por ejemplo list_for_sensor, que valide existencia, intervalo y consulta; el router debería invocarlo una sola vez. Mantener la ruta global como filtro independiente si esa diferencia es deliberada.

Regla física de temperatura mezclada en el servicio y aplicada antes de conocer el tipo — prioridad bajaUbicación: [app/services.py (line 161)](C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/services.py:161), [app/services.py (line 184)](C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/services.py:184), [app/services.py (line 236)](C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/services.py:236).
Responsabilidad actual: ReadingService aplica compatibilidad unidad/tipo, rango operativo y el límite de cero absoluto.
Problema: la regla de cero absoluto es una invariante de temperatura, pero se evalúa para cualquier lectura antes de cargar el sensor. domain.py ya concentra reglas puras de configuración, de modo que las reglas de lectura están divididas.
Por qué importa: un sensor de humedad configurado con un rango inferior a -273.15 recibiría un error de temperatura, aunque no sea una medición de temperatura. Es un caso de borde, pero ilustra que la regla no está ligada a su contexto.
Cambio recomendado: si el cero absoluto forma parte del dominio, moverlo a una validación pura del dominio que reciba el tipo de sensor y aplicarlo sólo a temperature. Es un ajuste de claridad y corrección, no una razón para crear entidades o patrones adicionales.

Mejoras opcionales
Manejo de errores HTTP repetido y contratos de ausencia inconsistentes — prioridad bajaUbicación: [app/routers.py (line 98)](C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/routers.py:98), [app/routers.py (line 240)](C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/routers.py:240), [app/services.py (line 67)](C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/services.py:67), [app/services.py (line 207)](C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/services.py:207).
Responsabilidad actual: los routers convierten excepciones o valores None en respuestas HTTP.
Problema: sensores inexistentes se expresan con ResourceNotFoundError, mientras lecturas inexistentes se expresan con None; el mapeo HTTP se repite en varios endpoints.
Por qué importa: hoy funciona y está cubierto por pruebas, pero aumenta la posibilidad de respuestas inconsistentes al crecer la API.
Cambio recomendado: unificar el contrato de servicios para ausencias y, sólo si la repetición aumenta, usar manejadores de excepciones de FastAPI. No es necesario introducir una jerarquía compleja de excepciones ahora.

Aspectos que están bien resueltos
Los repositorios concentran select, commit, rollback y detalles SQLAlchemy: [app/repositories.py (line 10)](C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/repositories.py:10).
Los routers no ejecutan SQL y usan inyección de dependencias para componer servicios y repositorios: [app/routers.py (line 39)](C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/routers.py:39).
La validación Pydantic reutiliza la misma regla de dominio que el servicio; no hay duplicación de lógica, sino validación de borde HTTP más defensa en profundidad: [app/schemas.py (line 16)](C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/schemas.py:16).
Las restricciones críticas están también en la base de datos —FK, cascada y unicidad—, no sólo en código: [app/models.py (line 25)](C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/models.py:25).
No hay evidencia de un problema actual de rendimiento o escalabilidad que justifique nueva infraestructura.
Veredicto: SensorHub necesita ajustes puntuales, no una refactorización importante. Priorizaría desacoplar gradualmente servicios del ORM y llevar la semántica de listado anidado al servicio; el resto puede evolucionar conforme aumenten los casos de uso.

### Comparación y veredicto
La principal diferencia que noté es que el prompt pobre deja a libre interpretación de la IA qué significa “hacer el código más eficiente”. En este caso, el modelo interpretó la eficiencia principalmente como rendimiento y escalabilidad, proponiendo optimizaciones para reducir consultas, manejar grandes cantidades de lecturas e incluso preparar el sistema para escenarios de mayor carga. Estas propuestas pueden ser técnicamente válidas, pero responden a problemas que todavía no hemos comprobado que existan ni son una prioridad para el alcance actual de SensorHub. En cambio, el prompt bueno delimitó que la revisión debía centrarse en separación de responsabilidades, acoplamiento y mantenibilidad. Esto hizo que la IA actuara más como un revisor de arquitectura, identificando problemas concretos del código actual y evitando proponer complejidad que el proyecto todavía no necesita.
---

## Tarea 3 — Análisis profundo de una mejora propuesta

### Prompt pobre
Analiza si conviene mover la validación de existencia del sensor al servicio cuando se listan sus lecturas y dime cómo lo implementarías.

### Resultado del prompt pobre
Sí, conviene. La existencia del sensor es una regla de negocio: hoy el endpoint la aplica en el router antes de delegar, mientras que creación y actualización ya la centralizan en ReadingService. Eso deja la regla duplicada y permite que otro consumidor del servicio liste lecturas de un sensor inexistente sin error.
Recomendaría no alterar ReadingService.list(...) directamente, porque también respalda GET /readings?sensor_id=..., que hoy puede comportarse como filtro global. En su lugar, añadiría un método explícito:
def list_for_sensor(
    self,
    sensor_id: str,
    offset: int,
    limit: int,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> list[ReadingModel]:
    self.require_sensor(sensor_id)
    return self.list(sensor_id, offset, limit, from_date, to_date)
Luego el endpoint anidado llamaría a service.list_for_sensor(...) y manejaría en un único try tanto ResourceNotFoundError (404) como InvalidDateRangeError (400). Se elimina así la validación actual del router en [routers.py (line 212)](C:\\Users\\ironm\\OneDrive\\Documentos\\EDSIA\\sdlc-electronica-jesus-castillo\\app\\routers.py:212).
Añadiría dos pruebas:
De servicio: list_for_sensor("UNKNOWN", ...) lanza ResourceNotFoundError.
De API: GET /sensors/UNKNOWN/readings responde 404, incluso si no hay lecturas.
Esto conserva el contrato de la ruta anidada y evita convertir accidentalmente GET /readings?sensor_id=UNKNOWN de 200 [] a 404. Si se desea que ese filtro también tenga semántica de “recurso hijo”, entonces sí se puede validar sensor_id dentro de list, pero sería un cambio de contrato que conviene versionar o documentar.
La prueba de servicios existente pasa (12 pruebas); el comando termina con fallo únicamente por el umbral global de cobertura al ejecutar ese archivo aislado.

### Prompt bueno
CONTEXTO:
SensorHub es una API REST en Python 3.12 con FastAPI y arquitectura por capas.
Actualmente, el endpoint anidado GET /sensors/{sensor_id}/readings valida en el
router que el sensor exista antes de llamar al servicio.

La revisión arquitectónica previa identificó que esta semántica del caso de
uso podría estar mejor encapsulada en la capa de servicio.

TAREA:
Analiza en profundidad si conviene mover esa responsabilidad al servicio y
cómo debería hacerse sin alterar contratos existentes de la API.

RESTRICCIONES:
- No modifiques archivos.
- Explica primero cuál es el comportamiento actual y por qué puede ser un
  problema arquitectónico.
- Identifica todos los endpoints, métodos, servicios y pruebas que podrían
  verse afectados.
- Distingue el comportamiento de la ruta anidada
  /sensors/{sensor_id}/readings frente al filtro global
  /readings?sensor_id=...
- No cambies comportamiento observable de la API salvo que lo justifiques
  explícitamente.
- Evalúa al menos dos alternativas de implementación.
- Para cada alternativa, indica ventajas, desventajas y riesgo de regresión.
- Indica qué pruebas existentes deberían conservarse y qué pruebas nuevas
  serían necesarias.
- Evalúa si el beneficio arquitectónico justifica el costo del cambio.
- Si la mejor decisión es no implementar el cambio, indícalo.
- Basa el análisis únicamente en evidencia del repositorio.

ENTREGA:
1. Comportamiento actual.
2. Problema arquitectónico.
3. Alcance del cambio.
4. Alternativas de implementación.
5. Riesgos y compatibilidad.
6. Pruebas necesarias.
7. Beneficios y costos.
8. Veredicto final: implementar, posponer o rechazar, con justificación.

### Resultado del prompt bueno
No modifiqué archivos. La decisión recomendada es implementar un ajuste pequeño y acotado: crear un caso de uso específico en ReadingService para listar lecturas de un sensor existente, sin cambiar ReadingService.list().
1. Comportamiento actual
GET /sensors/{sensor_id}/readings ejecuta, desde el router, service.require_sensor(sensor_id) y luego service.list(...). Si el sensor no existe, devuelve 404 {"detail":"Sensor no encontrado"}; si existe, filtra, pagina y aplica el rango de fechas. Véase [routers.py (line 201)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/routers.py:201).
ReadingService.list() no comprueba que exista el sensor: sólo valida que from <= to y delega el filtro al repositorio. [services.py (line 211)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/services.py:211). El repositorio genera una consulta filtrada si recibe sensor_id; para uno inexistente, el resultado es naturalmente una lista vacía. [repositories.py (line 105)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/repositories.py:105).
La ruta global GET /readings?sensor_id=... llama directamente a service.list(sensor_id, skip, limit) y no valida la existencia del sensor. Por tanto, según el código, GET /readings?sensor_id=UNKNOWN responde 200 [], no 404. [routers.py (line 225)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/routers.py:225).
Diferencias deliberadas actuales:
Aspecto	Ruta anidada	Filtro global
Ruta	/sensors/{id}/readings	/readings?sensor_id={id}
Sensor inexistente	404	200 []
Paginación por defecto	offset=0, limit=50	skip=0, limit=10
Filtros de fecha	from, to	No disponibles
Rol documentado	Canónica	Conservada por compatibilidad


2. Problema arquitectónico
La comprobación no accede directamente al repositorio desde el router —usa el método de servicio require_sensor()—, pero la semántica del caso de uso “listar lecturas de un recurso padre existente” está dividida:
El router conoce que la ruta anidada exige la existencia del sensor.
El servicio conoce cómo validar la existencia, pero list() no expresa ni garantiza esa precondición.
Eso contradice parcialmente la responsabilidad declarada por el proyecto: los endpoints manejan formato HTTP y respuestas HTTP, mientras el servicio contiene reglas y coordina operaciones. [README.md (line 49)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/README.md:49)
Además, ReadingService ya concentra esa regla para creación y actualización de lecturas mediante _validate_for_sensor() y require_sensor(). [services.py (line 155)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/app/services.py:155)
3. Alcance del cambio
Afectación directa:
GET /sensors/{sensor_id}/readings: debe conservar 404, filtrado, paginación y errores de fecha.
ReadingService: añadiría un método de caso de uso para la ruta anidada.
Router: sustituiría la secuencia manual require_sensor() + list() por una llamada al método nuevo, manteniendo la conversión de excepciones a HTTP.
Pruebas unitarias de servicio y pruebas de integración de la ruta anidada.
Afectación indirecta que debe vigilarse:
GET /readings?sensor_id=...: no debe cambiar; conserva su contrato de filtro global y compatibilidad.
POST /sensors/{id}/readings y POST /readings: ya verifican existencia dentro de record().
PATCH /readings/{id}: ya revalida contra el sensor mediante el servicio.
SensorRepository y ReadingRepository: no requieren cambios en la alternativa recomendada.
No se requieren migraciones, cambios de esquema, cambios OpenAPI ni cambios en rutas.
4. Alternativas de implementación
A. Método explícito list_for_sensor(...) en el servicio — recomendada
Conceptualmente:
def list_for_sensor(...):
    self.require_sensor(sensor_id)
    return self.list(sensor_id, offset, limit, from_date, to_date)
El router sólo llama este método y traduce ResourceNotFoundError a 404 e InvalidDateRangeError a 400.
Ventajas:
Encapsula la semántica de la ruta anidada en la capa de servicio.
Mantiene list() como consulta global/filtro, cuyo sensor_id puede ser inexistente.
No cambia interfaces de repositorio ni contratos HTTP.
Conserva el orden actual: para un sensor inexistente con fechas invertidas, primero se produce 404, como hoy.
Desventajas:
Añade un método público pequeño que comparte parte de la lógica con list().
La comprobación sigue siendo una consulta adicional a la lectura; ya existe hoy, por lo que no supone un costo nuevo.
Riesgo de regresión: bajo, si se conservan orden y mapeo de excepciones.
B. Añadir una bandera a list(), por ejemplo require_existing_sensor=False
La ruta anidada usaría list(..., require_existing_sensor=True) y la global mantendría el valor predeterminado.
Ventajas:
No añade otro método de servicio.
Centraliza la bifurcación en un solo método.
Desventajas:
Una bandera booleana vuelve ambiguo el contrato de list().
Facilita llamadas incorrectas y mezcla dos casos de uso distintos: colección global filtrable frente a subcolección de un recurso padre.
El cambio de firma afecta a dobles de prueba, consumidores internos y futuras implementaciones.
Riesgo de regresión: medio.
C. Hacer que list() siempre exija existencia cuando recibe sensor_id — no recomendable
Ventaja:
Código aparentemente más corto.
Desventaja principal:
Cambia GET /readings?sensor_id=UNKNOWN de 200 [] a 404, salvo que se añadan excepciones de flujo. Eso altera el contrato observable de una ruta que el README marca como compatible. [README.md (line 240)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/README.md:240)
Riesgo de regresión: alto. Debe rechazarse.
5. Riesgos y compatibilidad
El mayor riesgo no es técnico sino semántico: confundir la ruta anidada con el filtro global y cambiar el resultado de sensor inexistente.
También importa el orden de errores. Actualmente, la ruta anidada verifica el sensor antes de que list() valide un intervalo invertido. La alternativa A debe mantener ese orden. Las validaciones de forma de FastAPI (limit, offset, fechas mal formadas) siguen ocurriendo antes del cuerpo del endpoint y conservan 422.
El cambio no elimina una posible carrera entre verificar el sensor y listar sus lecturas si otro proceso lo borra inmediatamente después. Esa situación ya existe hoy y resolverla requeriría una decisión distinta de consistencia/transacción; no justifica ampliar este refactor.
6. Pruebas necesarias
Conservar:
Paginación, offset y filtro por sensor de la ruta anidada: test_nested_list_filters_sensor_and_uses_default_pagination y test_nested_list_applies_limit_and_offset. [test_main.py (line 224)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/tests/test_main.py:224)
Validación 422 de parámetros y 400 para fechas invertidas. [test_main.py (line 256)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/tests/test_main.py:256)
Prueba unitaria actual de intervalo invertido en ReadingService.list(). [test_services.py (line 294)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/tests/test_services.py:294)
Pruebas de creación que verifican existencia, pues prueban el uso existente de require_sensor(). [test_sensors.py (line 116)](/C:/Users/ironm/OneDrive/Documentos/EDSIA/sdlc-electronica-jesus-castillo/tests/test_sensors.py:116)
Añadir:
Unitaria: list_for_sensor("UNKNOWN", ...) lanza ResourceNotFoundError y no consulta ReadingRepository.list.
Unitaria: list_for_sensor() con sensor válido conserva filtrado, límites y fechas.
Integración: GET /sensors/UNKNOWN/readings devuelve exactamente 404 y "Sensor no encontrado". Esta cobertura falta actualmente.
Integración: GET /readings?sensor_id=UNKNOWN devuelve 200 []. Esta diferencia contractual tampoco está cubierta hoy.
Integración: sensor inexistente más from > to en la ruta anidada devuelve 404, para fijar el orden de errores actual.
7. Beneficios y costos
El beneficio es moderado pero real: cada caso de uso queda completo en la capa de servicio y resulta reutilizable fuera de FastAPI, sin repetir la secuencia de validación en futuros adaptadores.
El costo es bajo con la alternativa A: un método, un cambio puntual de llamada y unas pocas pruebas. No toca persistencia, API pública ni documentación funcional, salvo que se quiera documentar explícitamente el 404 de la ruta anidada.
8. Veredicto final
Implementar la alternativa A.
Es un refactor de bajo riesgo que corrige una frontera de responsabilidad concreta sin modificar contratos observables: la ruta anidada conserva 404 para sensor inexistente y el filtro global conserva 200 []. No recomiendo alterar ReadingService.list() para exigir existencia automáticamente, porque sí cambiaría la semántica de /readings?sensor_id=....

### Comparación y veredicto
La principal diferencia fue que el prompt pobre se centró rápidamente en resolver el problema concreto y propuso una implementación que intentaba conservar el comportamiento actual. Sin embargo, el prompt bueno analizó primero cómo afectaría el cambio al proyecto completo antes de recomendar una solución. Consideró los endpoints afectados, los contratos actuales de la API, las pruebas, los posibles riesgos de regresión y distintas alternativas de implementación. Esto me da mayor confianza porque la IA no solamente propone una solución que funciona, sino que evalúa si realmente mejora la organización del proyecto y si el beneficio justifica los cambios necesarios.