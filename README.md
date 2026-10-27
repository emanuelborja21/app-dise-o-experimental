# App de Diseño Experimental

Aplicación educativa en Python y Streamlit para apoyar el curso de Diseño Experimental del programa de Ingeniería Agrícola de la Universidad de Sucre.

## Descripción

La aplicación acompaña el análisis de diseños experimentales agrícolas. Permite cargar datos, revisar resultados estadísticos y explorar diagnósticos; su propósito es apoyar el aprendizaje, no reemplazar la interpretación del estudiante ni la verificación de supuestos y cálculos manuales.

## Módulos

| Código | Diseño | Estado |
| --- | --- | --- |
| DCA | Diseño Completamente al Azar | Disponible |
| DBCA | Diseño de Bloques Completos al Azar | En construcción |
| DCL | Diseño de Cuadrado Latino | En construcción |
| DPD | Diseño de Parcelas Divididas | En construcción |
| Factoriales | Diseños Factoriales | En construcción |
| RSM | Metodología de Superficie de Respuesta | En construcción |

## Estructura del proyecto

```text
.
├── app.py                         # Portada de la aplicación
├── pages/                         # Páginas de los diseños experimentales
├── utils/                         # Funciones reutilizables para análisis y diagnóstico
├── data/                          # Datos de ejemplo en CSV
├── verificacion/                  # Scripts de R para verificar análisis
├── requirements.txt               # Dependencias de Python
└── .github/copilot-instructions.md # Reglas para contribuir con el agente
```

## Instalación y ejecución local

En Windows, abre PowerShell en la carpeta del proyecto y ejecuta:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Instalación y ejecución en Codespaces

En la terminal del Codespace ejecuta:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Streamlit mostrará la dirección local de la aplicación en la terminal.

## Autoría

- Autor: Escribe aquí tu nombre
- Curso: Diseño Experimental
- Programa: Ingeniería Agrícola, Universidad de Sucre
- Semestre: 2026-2

## Uso de inteligencia artificial

Durante el desarrollo se utilizó GitHub Copilot como apoyo para estructurar y revisar código y documentación. Los análisis se ejecutan sobre los datos cargados; el estudiante debe interpretar los resultados, verificar los supuestos y contrastarlos con sus cálculos manuales.
