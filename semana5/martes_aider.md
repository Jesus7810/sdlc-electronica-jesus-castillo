# Aider: IA con trazabilidad Git

## Objetivo

El objetivo de esta actividad fue probar Aider como herramienta de desarrollo asistido por IA y entender su integración con Git, especialmente la posibilidad de mantener trazabilidad sobre los cambios realizados por la IA.

## Prueba con Aider

Instalé Aider siguiendo la documentación indicada:

```powershell
pip install aider-install
aider-install
```

La instalación terminó correctamente y verifiqué la versión:

```text
aider 0.86.2
```

Aider detectó el repositorio Git y recomendó agregar sus archivos auxiliares al `.gitignore`, por lo que se añadió:

```gitignore
.aider*
```

Después comprobé los modelos disponibles mediante GitHub Copilot:

```powershell
aider --list-models github
```

Aider detectó diferentes modelos y probé:

```text
github_copilot/gpt-5
```

Sin embargo, aunque se realizó el proceso de autenticación con GitHub, al intentar utilizar el modelo apareció repetidamente el error:

```text
litellm.AuthenticationError:
Failed to refresh API key after maximum retries
```

Después de comprobar que el problema se repetía, decidí no seguir invirtiendo tiempo en configurar otro proveedor.

La propia actividad permite utilizar Copilot Chat cuando no es posible configurar un modelo en Aider, por lo que continué el ejercicio mediante esa alternativa.

## Ejercicio con Copilot Chat

Utilicé Copilot Chat para crear un ejercicio aislado de conversiones entre Celsius y Fahrenheit.

Se crearon:

```text
semana5/conversions.py
semana5/test_conversions.py
```

Se mantuvo el ejercicio separado del código de SensorHub para no introducir una funcionalidad que el proyecto actualmente no necesita.

Las pruebas específicas del ejercicio dieron como resultado:

```text
8 passed
```

Ruff también terminó sin errores:

```text
All checks passed!
```

## ¿En qué supera Aider a Copilot?

Lo que me pareció más interesante de Aider es su integración directa con Git y, especialmente, los commits automáticos de los cambios realizados por la IA.

La capacidad de modificar archivos no me parece por sí sola una gran diferencia, porque herramientas integradas en VS Code también pueden hacerlo. Lo que considero más valioso de Aider es que está diseñado para mantener trazabilidad sobre qué cambios fueron realizados mediante IA.

En este ejercicio no pude comprobar completamente los commits automáticos debido al problema de autenticación del modelo, por lo que no puedo evaluar esta característica a partir de una ejecución completa.

## ¿En qué falla?

La principal desventaja que experimenté fue la configuración.

Aunque Aider se instaló correctamente y detectó tanto Git como los modelos disponibles, la autenticación con el modelo seleccionado falló repetidamente. Esto generó más fricción que Copilot Chat, que ya estaba integrado en VS Code y permitió continuar rápidamente con el ejercicio.

También considero que, independientemente de la herramienta utilizada, las respuestas y cambios de una IA deben verificarse. Durante el ejercicio con Copilot observé que algunas conclusiones podían parecer correctas y detalladas, pero necesitaban contrastarse con el código real del proyecto.

## Conclusión

Aider me pareció especialmente interesante por su enfoque en la trazabilidad Git, aunque no pude probar completamente su flujo de commits automáticos debido al problema de autenticación.

Copilot Chat fue más sencillo de utilizar en mi entorno actual y permitió completar el ejercicio, pero eso no elimina la necesidad de revisar sus propuestas y verificar los cambios mediante pruebas y herramientas de calidad.

La principal idea que me llevo de la actividad es que utilizar IA no significa delegar la responsabilidad sobre el código. La IA puede realizar o proponer cambios, pero el desarrollador sigue siendo responsable de entenderlos, verificarlos y decidir si deben formar parte del proyecto.