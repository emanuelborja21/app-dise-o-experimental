import json
import warnings
from itertools import combinations
from pathlib import Path
from typing import BinaryIO

import numpy as np
import pandas as pd
from scipy.stats import studentized_range
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.regression.linear_model import RegressionResultsWrapper


def cargar_datos(archivo: str | Path | BinaryIO) -> pd.DataFrame:
    """Carga un archivo CSV o Excel en un DataFrame.

    Args:
        archivo: Ruta del archivo o archivo binario abierto.

    Returns:
        Datos leídos desde el archivo.

    Raises:
        ValueError: Si el formato no es CSV ni XLSX.
    """
    nombre = getattr(archivo, "name", str(archivo))
    extension = Path(nombre).suffix.lower()
    if hasattr(archivo, "seek"):
        archivo.seek(0)

    if extension == ".xlsx":
        return pd.read_excel(archivo)
    if extension == ".csv" or not extension:
        # pandas infiere si los campos del CSV están separados por coma o punto y coma.
        return pd.read_csv(archivo, sep=None, engine="python")
    raise ValueError("El archivo debe tener formato CSV o XLSX.")


def validar_dca(df: pd.DataFrame, col_trat: str, col_resp: str) -> list[str]:
    """Valida los datos requeridos para un diseño completamente al azar.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna con la respuesta numérica.

    Returns:
        Mensajes de error encontrados; la lista queda vacía si los datos son válidos.
    """
    errores: list[str] = []
    columnas_faltantes = [
        columna for columna in (col_trat, col_resp) if columna not in df.columns
    ]
    if columnas_faltantes:
        errores.append(f"Faltan las columnas requeridas: {', '.join(columnas_faltantes)}.")
        return errores

    if not pd.api.types.is_numeric_dtype(df[col_resp]):
        errores.append(f"La respuesta '{col_resp}' debe ser numérica.")
    if df[[col_trat, col_resp]].isna().any().any():
        errores.append("Hay datos faltantes en las columnas de tratamiento o respuesta.")

    numero_tratamientos = df[col_trat].nunique(dropna=True)
    # Un DCA compara al menos dos tratamientos: k >= 2.
    if numero_tratamientos < 2:
        errores.append("Se requieren al menos dos tratamientos.")

    # Cada media de tratamiento necesita al menos dos réplicas: n_i >= 2.
    conteos = df[col_trat].value_counts(dropna=True)
    tratamientos_insuficientes = conteos[conteos < 2].index.tolist()
    if tratamientos_insuficientes:
        nombres = ", ".join(str(tratamiento) for tratamiento in tratamientos_insuficientes)
        errores.append(f"Cada tratamiento necesita al menos dos réplicas; revise: {nombres}.")

    return errores


def ajustar_dca(
    df: pd.DataFrame, col_trat: str, col_resp: str
) -> RegressionResultsWrapper:
    """Ajusta el modelo lineal de un diseño completamente al azar.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna con la respuesta numérica.

    Returns:
        Modelo OLS ajustado.

    Raises:
        ValueError: Si los datos no cumplen los requisitos del DCA.
    """
    errores = validar_dca(df, col_trat, col_resp)
    if errores:
        raise ValueError(" ".join(errores))

    # Modelo: Y_ij = mu + tau_i + epsilon_ij; Q protege nombres arbitrarios de columnas.
    formula = f'Q({json.dumps(col_resp)}) ~ C(Q({json.dumps(col_trat)}))'
    return ols(formula=formula, data=df).fit()


def tabla_anova(modelo: RegressionResultsWrapper) -> pd.DataFrame:
    """Construye la tabla ANOVA tipo II y agrega la variación total.

    Args:
        modelo: Modelo OLS ajustado para un DCA.

    Returns:
        Tabla con las fuentes, grados de libertad, sumas y cuadrados medios, F y p-valor.
    """
    tabla_modelo = anova_lm(modelo, typ=2)
    filas_tratamiento = tabla_modelo.drop(index="Residual", errors="ignore")
    if len(filas_tratamiento) != 1 or "Residual" not in tabla_modelo.index:
        raise ValueError("El modelo debe contener un único factor y su error residual.")

    tratamiento = filas_tratamiento.iloc[0]
    error = tabla_modelo.loc["Residual"]
    gl_tratamiento = float(tratamiento["df"])
    gl_error = float(error["df"])
    sc_tratamiento = float(tratamiento["sum_sq"])
    sc_error = float(error["sum_sq"])
    sc_total = sc_tratamiento + sc_error
    gl_total = gl_tratamiento + gl_error

    # En cada fuente, CM = SC / gl; la variación total suma tratamientos y error.
    filas = [
        {
            "Fuente": "Tratamientos",
            "gl": gl_tratamiento,
            "SC": sc_tratamiento,
            "CM": sc_tratamiento / gl_tratamiento,
            "F": float(tratamiento["F"]),
            "p-valor": float(tratamiento["PR(>F)"]),
        },
        {
            "Fuente": "Error",
            "gl": gl_error,
            "SC": sc_error,
            "CM": sc_error / gl_error,
            "F": np.nan,
            "p-valor": np.nan,
        },
        {
            "Fuente": "Total",
            "gl": gl_total,
            "SC": sc_total,
            "CM": sc_total / gl_total,
            "F": np.nan,
            "p-valor": np.nan,
        },
    ]
    return pd.DataFrame(filas, columns=["Fuente", "gl", "SC", "CM", "F", "p-valor"])


def resumen_tratamientos(
    df: pd.DataFrame, col_trat: str, col_resp: str
) -> pd.DataFrame:
    """Resume el tamaño de muestra y la respuesta por tratamiento.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna con la respuesta numérica.

    Returns:
        Conteo, total, media y desviación estándar de cada tratamiento.
    """
    # Para cada tratamiento, n cuenta réplicas; total = suma(y), media = total / n.
    resumen = df.groupby(col_trat, dropna=False)[col_resp].agg(
        ["count", "sum", "mean", "std"]
    )
    # La desviación estándar muestral resume la dispersión de réplicas alrededor de la media.
    return (
        resumen.rename(
            columns={
                "count": "n",
                "sum": "total",
                "mean": "media",
                "std": "desviación estándar",
            }
        )
        .rename_axis(col_trat)
        .reset_index()
    )


def coeficiente_variacion(
    modelo: RegressionResultsWrapper, df: pd.DataFrame, col_resp: str
) -> float:
    """Calcula el coeficiente de variación residual del experimento.

    Args:
        modelo: Modelo OLS ajustado para un DCA.
        df: Datos del experimento.
        col_resp: Nombre de la columna con la respuesta numérica.

    Returns:
        Coeficiente de variación expresado como porcentaje.

    Raises:
        ValueError: Si la media general de la respuesta es cero.
    """
    cme = float(modelo.mse_resid)
    media_general = float(df[col_resp].mean())
    if media_general == 0:
        raise ValueError("El coeficiente de variación no se define si la media es cero.")

    # CV = sqrt(CME) / media general * 100; expresa el error respecto al nivel de respuesta.
    return float(np.sqrt(cme) / media_general * 100)


def tukey(
    df: pd.DataFrame,
    col_trat: str,
    col_resp: str,
    alfa: float = 0.05,
) -> tuple[pd.DataFrame, float]:
    """Compara medias con Tukey y calcula una diferencia mínima significativa.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna con la respuesta numérica.
        alfa: Nivel de significancia entre cero y uno.

    Returns:
        Una tabla de comparaciones de Tukey y la DMS.

    Raises:
        ValueError: Si alfa o los datos no son válidos para el análisis.
    """
    if not 0 < alfa < 1:
        raise ValueError("Alfa debe estar entre cero y uno.")
    errores = validar_dca(df, col_trat, col_resp)
    if errores:
        raise ValueError(" ".join(errores))

    comparacion = pairwise_tukeyhsd(
        endog=df[col_resp], groups=df[col_trat], alpha=alfa
    )
    grupos = list(comparacion.groupsunique)
    pares = list(combinations(range(len(grupos)), 2))
    tabla = pd.DataFrame(
        {
            "Tratamiento 1": [grupos[primero] for primero, _ in pares],
            "Tratamiento 2": [grupos[segundo] for _, segundo in pares],
            "Diferencia de medias": comparacion.meandiffs,
            "p-valor ajustado": comparacion.pvalues,
            "Límite inferior": comparacion.confint[:, 0],
            "Límite superior": comparacion.confint[:, 1],
            "Rechaza H₀": comparacion.reject,
        }
    )

    modelo = ajustar_dca(df, col_trat, col_resp)
    conteos = df.groupby(col_trat).size()
    balanceado = conteos.nunique() == 1
    if balanceado:
        replicas = float(conteos.iloc[0])
    else:
        # En datos desbalanceados, la media armónica de n_i aproxima una réplica común r.
        replicas = float(len(conteos) / sum(1 / conteo for conteo in conteos))
        warnings.warn(
            "El diseño no está balanceado; la DMS calculada es aproximada.",
            UserWarning,
            stacklevel=2,
        )

    # DMS = q_(1-alfa; k, glE) * sqrt(CME / r), con q de rango studentizado.
    q_critico = studentized_range.ppf(
        1 - alfa, len(conteos), float(modelo.df_resid)
    )
    dms = float(q_critico * np.sqrt(float(modelo.mse_resid) / replicas))
    return tabla, dms


def interpretar_dca(tabla: pd.DataFrame, alfa: float = 0.05) -> str:
    """Interpreta la prueba F del factor en un DCA.

    Args:
        tabla: Tabla ANOVA con las columnas ``Fuente`` y ``p-valor``.
        alfa: Nivel de significancia entre cero y uno.

    Returns:
        Explicación sencilla de la decisión sobre las medias de tratamientos.

    Raises:
        ValueError: Si alfa no es válido o la tabla no contiene el resultado requerido.
    """
    if not 0 < alfa < 1:
        raise ValueError("Alfa debe estar entre cero y uno.")
    if not {"Fuente", "p-valor"}.issubset(tabla.columns):
        raise ValueError("La tabla debe incluir las columnas 'Fuente' y 'p-valor'.")

    fila = tabla.loc[tabla["Fuente"] == "Tratamientos", "p-valor"]
    if fila.empty or pd.isna(fila.iloc[0]):
        raise ValueError("La tabla no contiene un p-valor válido para Tratamientos.")

    p_valor = float(fila.iloc[0])
    # Regla: rechazar H0: mu_1 = ... = mu_k cuando p-valor <= alfa.
    if p_valor <= alfa:
        return (
            f"Se rechaza H₀ (p-valor = {p_valor:.4g} <= alfa = {alfa:.4g}). "
            "Hay evidencia de que al menos una media de tratamiento difiere; "
            "considere esa diferencia al decidir y use una comparación de medias."
        )
    return (
        f"No se rechaza H₀ (p-valor = {p_valor:.4g} > alfa = {alfa:.4g}). "
        "No hay evidencia suficiente de diferencias entre las medias; "
        "esto no demuestra que los tratamientos sean idénticos."
    )