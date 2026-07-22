# Scrum Guide 2020 — Conceptos principales

## 1. Responsabilidades del Scrum Team

Aunque normalmente se conocen como roles, la Scrum Guide 2020 los presenta como responsabilidades dentro del Scrum Team.

### Product Owner

Es responsable de maximizar el valor del producto y administrar el Product Backlog. Decide qué elementos tienen mayor prioridad, pero no determina cómo deben implementarlos técnicamente los Developers.

### Developers

Son responsables de crear un Increment útil y de calidad durante cada Sprint. Ellos organizan su trabajo, crean el Sprint Backlog y deciden cómo implementar la solución.

### Scrum Master

Es responsable de ayudar al equipo y a la organización a comprender y aplicar Scrum correctamente. También ayuda a eliminar impedimentos y a mejorar la efectividad del Scrum Team.

Una forma sencilla de recordarlos es:

- **Product Owner:** decide qué aporta mayor valor.
- **Developers:** deciden cómo construirlo.
- **Scrum Master:** ayuda a que Scrum se aplique correctamente.

## 2. Eventos de Scrum y sus timeboxes

### Sprint

Es el evento que contiene a todos los demás. Durante este periodo, el equipo trabaja para alcanzar el Sprint Goal y crear un Increment útil.

- **Timebox:** un mes o menos.

### Sprint Planning

El Scrum Team define por qué es valioso el Sprint, qué trabajo puede realizarse y cómo se llevará a cabo.

- **Timebox máximo:** 8 horas para un Sprint de un mes.

### Daily Scrum

Los Developers inspeccionan su progreso hacia el Sprint Goal y adaptan su plan de trabajo.

- **Timebox:** 15 minutos diarios.

### Sprint Review

El Scrum Team y las personas interesadas inspeccionan el resultado del Sprint y determinan posibles cambios para el producto.

- **Timebox máximo:** 4 horas para un Sprint de un mes.

### Sprint Retrospective

El Scrum Team analiza su manera de trabajar y propone mejoras para aumentar la calidad y efectividad.

- **Timebox máximo:** 3 horas para un Sprint de un mes.

Para Sprints más cortos, los eventos normalmente también tienen una duración menor.

## 3. Artefactos y sus compromisos

### Product Backlog

Es la lista ordenada del trabajo necesario para mejorar el producto.

- **Compromiso:** Product Goal.
- El Product Goal representa el objetivo futuro del producto.

### Sprint Backlog

Contiene el Sprint Goal, los elementos seleccionados del Product Backlog y el plan para realizarlos.

- **Compromiso:** Sprint Goal.
- El Sprint Goal representa el objetivo que se busca alcanzar durante el Sprint.

### Increment

Es el resultado útil y verificable creado durante el Sprint. Se suma a los incrementos anteriores y debe estar en condiciones de uso.

- **Compromiso:** Definition of Done.
- Un trabajo que no cumple la Definition of Done no puede considerarse parte del Increment.

## 4. Valores de Scrum

### Compromiso

Los integrantes se comprometen con los objetivos del equipo y con realizar un trabajo de calidad.

### Enfoque

El equipo concentra sus esfuerzos en el trabajo y en el objetivo del Sprint.

### Apertura

Los integrantes comunican honestamente sus avances, dificultades e impedimentos.

### Respeto

Cada integrante reconoce las capacidades, responsabilidades e ideas de los demás.

### Coraje

El equipo enfrenta los problemas, reconoce los errores y toma decisiones difíciles cuando es necesario.

## 5. Definition of Done y criterios de aceptación

### Definition of Done

Es el conjunto de condiciones generales de calidad que debe cumplir todo trabajo para considerarse terminado y formar parte del Increment.

Ejemplos:

- todos los tests pasan;
- se alcanza la cobertura mínima requerida;
- `ruff` y `mypy` no reportan errores;
- el código fue revisado;
- la documentación está actualizada.

### Criterios de aceptación

Son las condiciones específicas que debe cumplir una funcionalidad o historia para satisfacer la necesidad del usuario.

Ejemplo:

> Dado un sensor que no está registrado, cuando se registra con un identificador válido, entonces debe quedar disponible para consulta.

### Diferencia

Los criterios de aceptación comprueban el comportamiento particular solicitado para una funcionalidad. La Definition of Done comprueba las condiciones generales de calidad aplicables a todo el trabajo.

Una funcionalidad puede cumplir sus criterios de aceptación y todavía no estar terminada. Por ejemplo, puede funcionar como se solicitó, pero si sus pruebas fallan o no alcanza la cobertura requerida, no cumple la Definition of Done.