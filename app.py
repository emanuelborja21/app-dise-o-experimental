import streamlit as st

AUTOR = "Escribe aquí tu nombre"

st.set_page_config(
    page_title="App de Diseño Experimental",
    page_icon="🌱",
    layout="wide",
)

st.title("Diseño Experimental en Ingeniería Agrícola")
st.subheader("Ingeniería Agrícola – Universidad de Sucre")
st.write(
    "El diseño experimental permite planear ensayos de campo de forma ordenada, "
    "comparar tratamientos con criterios claros y obtener evidencia útil para "
    "tomar decisiones sobre cultivos, suelos y prácticas agrícolas."
)

st.header("Módulos")
st.table(
    [
        {
            "Módulo": "DCA",
            "Nombre completo": "Diseño Completamente al Azar",
            "Cuándo se usa": "Cuando las unidades experimentales son homogéneas y los tratamientos se asignan al azar.",
            "Ejemplo agrícola": "Comparar fertilizantes en parcelas uniformes de un lote de maíz.",
            "Estado": "Disponible",
        },
        {
            "Módulo": "DBCA",
            "Nombre completo": "Diseño de Bloques Completos al Azar",
            "Cuándo se usa": "Cuando se puede agrupar las unidades para controlar una fuente conocida de variación.",
            "Ejemplo agrícola": "Comparar variedades de fríjol en bloques definidos por un gradiente de fertilidad.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "DCL",
            "Nombre completo": "Diseño de Cuadrado Latino",
            "Cuándo se usa": "Cuando se deben controlar dos fuentes de variación mediante filas y columnas.",
            "Ejemplo agrícola": "Comparar variedades de arroz controlando gradientes de suelo y humedad.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "DPD",
            "Nombre completo": "Diseño de Parcelas Divididas",
            "Cuándo se usa": "Cuando dos factores se aplican en unidades experimentales de distinto tamaño o con distinta facilidad.",
            "Ejemplo agrícola": "Evaluar sistemas de labranza en parcelas principales y dosis de fertilizante en subparcelas.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "Factoriales",
            "Nombre completo": "Diseños Factoriales",
            "Cuándo se usa": "Cuando se estudian simultáneamente varios factores y sus posibles interacciones.",
            "Ejemplo agrícola": "Evaluar combinaciones de dosis de nitrógeno y variedades de arroz.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "RSM",
            "Nombre completo": "Metodología de Superficie de Respuesta",
            "Cuándo se usa": "Cuando se busca modelar y optimizar una respuesta en función de factores cuantitativos.",
            "Ejemplo agrícola": "Estimar combinaciones de riego y fertilización que favorezcan el rendimiento de un cultivo.",
            "Estado": "En construcción",
        },
    ]
)

st.header("Cómo usar la aplicación")
st.markdown(
    "1. Elige un módulo en el menú lateral.\n"
    "2. Carga los datos del ensayo siguiendo las indicaciones del módulo.\n"
    "3. Revisa los resultados y su interpretación.\n"
    "4. Verifica los procedimientos y resultados con tu cálculo manual."
)

st.warning(
    "Esta app apoya el aprendizaje. El estudiante interpreta los resultados, "
    "verifica supuestos y compara con su cálculo manual."
)

st.sidebar.title("Información académica")
st.sidebar.write(f"Autor: {AUTOR}")
st.sidebar.write("Curso: Diseño Experimental")
st.sidebar.write("Semestre: 2026-2")
