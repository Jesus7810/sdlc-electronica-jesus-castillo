# Definition of Done

Una historia de usuario se considera terminada cuando cumple con todos los siguientes criterios:

- Sus criterios de aceptación en Gherkin están representados mediante pruebas automatizadas.
- Todas las pruebas pasan correctamente con pytest.
- La cobertura del código es igual o superior al 80 %.
- Ruff no reporta errores.
- mypy no reporta errores de tipos.
- El código utiliza nombres claros y mantiene una estructura sencilla y organizada.
- El diff del Pull Request fue revisado línea por línea antes de realizar el merge.
- La documentación relacionada con el cambio está actualizada.

Si alguna de estas condiciones no se cumple, la historia permanece en Review y todavía no puede considerarse Done.