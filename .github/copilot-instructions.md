# Instrucciones permanentes del repositorio

## Contexto del proyecto
- Este proyecto es una aplicación de Diseño Experimental desarrollada en Python y Streamlit para el curso de Diseño Experimental de Ingeniería Agrícola de la Universidad de Sucre.
- La estructura esperada es:
  - `app.py`: portada de la aplicación.
  - `pages/`: un archivo por cada diseño experimental.
  - `utils/`: funciones reutilizables; debe incluir `__init__.py`.
  - `data/`: archivos CSV de ejemplo.
  - `verificacion/`: scripts de R para verificar los análisis.

## Idioma y explicación estadística
- Escribe todo el código, los comentarios, los docstrings y los mensajes de la interfaz en español.
- Añade un comentario en cada paso estadístico que explique qué se calcula y por qué, con una explicación adecuada para estudiantes de Ingeniería Agrícola.
- No inventes ni escribas resultados de ejemplo como si fueran resultados calculados. Todos los números presentados deben provenir del cálculo realizado con los datos.

## Código Python
- Define anotaciones de tipos (`type hints`) en las funciones.
- Escribe los docstrings de las funciones en español y con el estilo Google.
- Limita las dependencias a `streamlit`, `pandas`, `numpy`, `scipy`, `statsmodels`, `plotly` y `openpyxl`. No agregues ni uses otras librerías sin pedir permiso.

## Análisis estadístico
- Ajusta los modelos de ANOVA con `statsmodels.formula.api.ols` y calcula la tabla con `statsmodels.stats.anova.anova_lm`, especificando `typ=2`.
- Realiza las comparaciones de Tukey con `statsmodels.stats.multicomp.pairwise_tukeyhsd`.

## Verificación
- Antes de terminar cada tarea, ejecuta el código pertinente y corrige los errores que aparezcan.
- Si el cambio no contiene código ejecutable o el repositorio aún no tiene código para ejecutar, indícalo y valida directamente los archivos modificados.
