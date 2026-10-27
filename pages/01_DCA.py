from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.anova_utils import (
	ajustar_dca,
	cargar_datos,
	coeficiente_variacion,
	f_critica_dca,
	interpretar_dca,
	resumen_tratamientos,
	tabla_anova,
	tukey,
	validar_dca,
)
from utils.diagnostico_utils import (
	grafico_qq,
	grafico_residuos_vs_ajustados,
	prueba_levene,
	prueba_shapiro,
	residuos_y_ajustados,
)


@st.cache_data(show_spinner=False)
def cargar_archivo(nombre_archivo: str, contenido: bytes | None = None) -> pd.DataFrame:
	"""Carga un archivo desde disco o desde el contenido recibido en la interfaz.

	Args:
		nombre_archivo: Nombre o ruta del archivo CSV o Excel.
		contenido: Bytes del archivo cargado; si es ``None``, se lee desde disco.

	Returns:
		Datos tabulares del experimento.
	"""
	if contenido is None:
		return cargar_datos(nombre_archivo)

	archivo = BytesIO(contenido)
	archivo.name = nombre_archivo
	return cargar_datos(archivo)


st.title("Diseño Completamente al Azar (DCA)")
st.write(
	"El Diseño Completamente al Azar compara tratamientos asignados al azar a "
	"unidades experimentales homogéneas. En este ejemplo se comparan cuatro "
	"secadores solares según la humedad final de la yuca (% b.h.), con cuatro "
	"réplicas por secador."
)

archivo_subido = st.file_uploader(
	"Cargar datos del experimento",
	type=["csv", "xlsx"],
)

if archivo_subido is None:
	st.caption("No se cargó un archivo; se usan los datos de ejemplo data/dca_secadores.csv.")
	ruta_ejemplo = Path(__file__).resolve().parents[1] / "data" / "dca_secadores.csv"
	nombre_archivo = str(ruta_ejemplo)
	contenido_archivo = None
else:
	nombre_archivo = archivo_subido.name
	contenido_archivo = archivo_subido.getvalue()

try:
	datos = cargar_archivo(nombre_archivo, contenido_archivo)
	datos.columns = datos.columns.map(str)
except Exception as error:
	st.error(f"No fue posible leer el archivo: {error}")
	st.stop()

if len(datos.columns) == 0:
	st.error("El archivo no contiene columnas para analizar.")
	st.stop()

columnas = datos.columns.tolist()
indice_tratamiento = next(
	(indice for indice, columna in enumerate(columnas) if columna.lower() in {"secador", "tratamiento"}),
	0,
)
columnas_numericas = [
	columna for columna in columnas if pd.api.types.is_numeric_dtype(datos[columna])
]
if "humedad" in columnas:
	indice_respuesta = columnas.index("humedad")
elif columnas_numericas:
	indice_respuesta = columnas.index(columnas_numericas[0])
else:
	indice_respuesta = 0

columna_tratamiento = st.selectbox(
	"Columna de tratamiento",
	columnas,
	index=indice_tratamiento,
)
columna_respuesta = st.selectbox(
	"Columna de respuesta",
	columnas,
	index=indice_respuesta,
)
alfa = st.slider(
	"Nivel de significancia (alfa)",
	min_value=0.01,
	max_value=0.10,
	value=0.05,
	step=0.01,
	format="%.2f",
)

# Validar estructura y réplicas evita ajustar un DCA cuando sus medias no son estimables.
errores = validar_dca(datos, columna_tratamiento, columna_respuesta)
if errores:
	for error in errores:
		st.error(error)
	st.stop()

# El modelo y la tabla ANOVA permiten evaluar si las medias de los secadores difieren.
modelo = ajustar_dca(datos, columna_tratamiento, columna_respuesta)
tabla = tabla_anova(modelo)
fila_tratamientos = tabla.loc[tabla["Fuente"] == "Tratamientos"].iloc[0]
p_valor = float(fila_tratamientos["p-valor"])
f_critica = f_critica_dca(modelo, alfa)
cv = coeficiente_variacion(modelo, datos, columna_respuesta)
resumen = resumen_tratamientos(datos, columna_tratamiento, columna_respuesta)
# Los residuos del modelo se usan para revisar normalidad y patrones de dispersión.
datos_residuos = residuos_y_ajustados(modelo)
estadistico_shapiro, p_shapiro, conclusion_shapiro = prueba_shapiro(
	datos_residuos["Residuos"], alfa
)
estadistico_levene, p_levene, conclusion_levene = prueba_levene(
	datos,
	columna_tratamiento,
	columna_respuesta,
	alfa,
)
tabla_supuestos = pd.DataFrame(
	[
		{
			"Prueba": "Shapiro-Wilk",
			"Estadístico": estadistico_shapiro,
			"p-valor": p_shapiro,
			"Conclusión": conclusion_shapiro,
		},
		{
			"Prueba": "Levene",
			"Estadístico": estadistico_levene,
			"p-valor": p_levene,
			"Conclusión": conclusion_levene,
		},
	]
)

pestana_datos, pestana_anova, pestana_comparaciones, pestana_graficos, pestana_supuestos = st.tabs(
	["Datos", "ANOVA", "Comparaciones", "Gráficos", "Supuestos"]
)

with pestana_datos:
	st.subheader("Datos del experimento")
	st.dataframe(datos, width="stretch", hide_index=True)
	st.subheader("Resumen por tratamiento")
	st.dataframe(resumen, width="stretch", hide_index=True)

with pestana_anova:
	st.subheader("Análisis de varianza")
	columnas_numericas_anova = tabla.select_dtypes(include="number").columns
	formato_anova = {columna: "{:.4f}" for columna in columnas_numericas_anova}
	st.dataframe(
		tabla.style.format(formato_anova),
		width="stretch",
		hide_index=True,
	)
	columna_f, columna_f_critica, columna_cv = st.columns(3)
	columna_f.metric("F observado", f"{float(fila_tratamientos['F']):.4f}")
	columna_f_critica.metric("F crítica", f"{f_critica:.4f}")
	columna_cv.metric("Coeficiente de variación", f"{cv:.4f}%")

	# La comparación del p-valor con alfa comunica la decisión de la prueba F.
	interpretacion = interpretar_dca(tabla, alfa)
	if p_valor < alfa:
		st.success(interpretacion)
	else:
		st.info(interpretacion)

with pestana_comparaciones:
	st.subheader("Comparaciones múltiples de Tukey")
	if p_valor < alfa:
		comparaciones, diferencia_minima = tukey(
			datos,
			columna_tratamiento,
			columna_respuesta,
			alfa,
		)
		columnas_numericas_tukey = comparaciones.select_dtypes(include="number").columns
		formato_tukey = {
			columna: "{:.4f}" for columna in columnas_numericas_tukey
		}
		st.dataframe(
			comparaciones.style.format(formato_tukey),
			width="stretch",
			hide_index=True,
		)
		st.metric("Diferencia mínima significativa (DMS)", f"{diferencia_minima:.4f}")
	else:
		st.info(
			"No se realiza Tukey porque el ANOVA no detectó diferencias "
			"estadísticamente significativas entre tratamientos al nivel alfa seleccionado."
		)

with pestana_graficos:
	st.subheader("Distribución de la respuesta por tratamiento")
	grafico_cajas = px.box(
		datos,
		x=columna_tratamiento,
		y=columna_respuesta,
		points="all",
		title="Respuesta por tratamiento",
		labels={
			columna_tratamiento: "Tratamiento",
			columna_respuesta: "Respuesta",
		},
	)
	st.plotly_chart(grafico_cajas, width="stretch")

	st.subheader("Medias por tratamiento")
	grafico_medias = px.bar(
		resumen,
		x=columna_tratamiento,
		y="media",
		error_y="desviación estándar",
		title="Media y desviación estándar por tratamiento",
		labels={
			columna_tratamiento: "Tratamiento",
			"media": "Media de la respuesta",
			"desviación estándar": "Desviación estándar",
		},
	)
	st.plotly_chart(grafico_medias, width="stretch")

with pestana_supuestos:
	st.subheader("Diagnóstico de supuestos del DCA")
	st.markdown(
		"**Normalidad:** Shapiro-Wilk evalúa si los residuos son compatibles con una "
		"distribución normal. El gráfico Q-Q permite revisar visualmente su alineación "
		"con los cuantiles normales."
	)
	st.plotly_chart(
		grafico_residuos_vs_ajustados(datos_residuos),
		width="stretch",
	)
	st.plotly_chart(grafico_qq(datos_residuos["Residuos"]), width="stretch")

	st.markdown(
		"**Homogeneidad de varianzas:** Levene, centrada en la mediana, contrasta si la "
		"variabilidad de la respuesta es similar entre tratamientos."
	)
	formato_supuestos = {
		"Estadístico": "{:.4f}",
		"p-valor": "{:.4f}",
	}
	st.dataframe(
		tabla_supuestos.style.format(formato_supuestos),
		width="stretch",
		hide_index=True,
	)

	st.markdown(
		"**Independencia por aleatorización:** se sustenta en la asignación aleatoria "
		"de las unidades experimentales y en que no interfieran entre sí. No se determina "
		"con Shapiro-Wilk ni con Levene; debe revisarse cómo se condujo el ensayo."
	)
