# ADR 0001: Arquitectura en capas para SensorHub

## Estado

Aceptado.

## Contexto

SensorHub utiliza FastAPI, SQLAlchemy, SQLite/PostgreSQL, Alembic y Pytest. Para evitar que los endpoints HTTP, las reglas de negocio y el acceso a datos queden mezclados, se define una separación explícita de responsabilidades.

Esta separación busca facilitar las pruebas de la lógica de negocio, reducir el acoplamiento entre componentes y reducir el impacto de los cambios de persistencia sobre las reglas de negocio.

## Decisión

Se adopta una arquitectura en capas con el siguiente flujo:

```text
routers -> services -> repositories -> models/SQLAlchemy -> database
```

Responsabilidades por capa:

- **routers:** gestionan HTTP, parámetros, request/response y traducen errores a códigos HTTP.
- **services:** implementan los casos de uso y las reglas de negocio.
- **repositories:** encapsulan la persistencia y las consultas mediante SQLAlchemy.
- **models/SQLAlchemy:** representan el mapeo de datos utilizado para acceder a SQLite o PostgreSQL.
- **database:** almacena los datos; Alembic administra las migraciones.

## Consecuencias

### Positivas

- Se evita mezclar la lógica HTTP, las reglas de negocio y la persistencia en los mismos módulos.
- La separación de responsabilidades facilita probar la lógica de negocio de forma más aislada.
- Se reduce el acoplamiento entre FastAPI y el acceso a datos con SQLAlchemy.
- La separación reduce el impacto de los cambios de persistencia sobre las reglas de negocio.
- Los endpoints permanecen enfocados en la interfaz HTTP y en la traducción de errores.

### Negativas

- El proyecto tendrá más archivos y módulos.
- Habrá más capas de indirección al seguir el flujo entre router, servicio y repositorio.
- Las funcionalidades pequeñas requerirán más ceremonia para mantener la separación de responsabilidades.
