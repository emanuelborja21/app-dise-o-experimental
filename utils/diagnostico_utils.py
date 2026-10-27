from collections.abc import Sequence

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from statsmodels.regression.linear_model import RegressionResultsWrapper

from utils.anova_utils import validar_dca


def residuos_y_ajustados(modelo: RegressionResultsWrapper) -> pd.DataFrame:
    """Extrae valores ajustados y residuos de un modelo OLS.

    Args:
        modelo: Modelo lineal ajustado para el experimento.

    Returns:
        DataFrame con las columnas ``Ajustados`` y ``Residuos``.
    """
    # El residuo e_i = y_i - y_estimado_i permite revisar patrones no explicados por el modelo.
    return pd.DataFrame(
        {
            "Ajustados": np.asarray(modelo.fittedvalues, dtype=float),
            "Residuos": np.asarray(modelo.resid, dtype=float),
        }
    )


def prueba_shapiro(
    residuos: Sequence[float] | np.ndarray | pd.Series,
    alfa: float = 0.05,
) -> tuple[float, float, str]:
    """Evalúa la normalidad de los residuos con Shapiro-Wilk.

    Args:
        residuos: Residuos del modelo.
        alfa: Nivel de significancia entre cero y uno.

    Returns:
        Estadístico W, p-valor y conclusión en español.

    Raises:
        ValueError: Si alfa no es válido, hay valores no finitos o menos de tres residuos.
    """
    if not 0 < alfa < 1:
        raise ValueError("Alfa debe estar entre cero y uno.")
    muestra = np.asarray(residuos, dtype=float)
    if muestra.ndim != 1 or not np.isfinite(muestra).all():
        raise ValueError("Los residuos deben ser una lista unidimensional de valores finitos.")
    if muestra.size < 3:
        raise ValueError("Shapiro-Wilk requiere al menos tres residuos.")

    # Shapiro-Wilk contrasta H0 de normalidad de los residuos mediante el estadístico W.
    resultado = stats.shapiro(muestra)
    estadistico = float(resultado.statistic)
    p_valor = float(resultado.pvalue)
    if p_valor < alfa:
        conclusion = (
            f"Se rechaza la normalidad de los residuos (p-valor = {p_valor:.4g} < "
            f"alfa = {alfa:.4g})."
        )
    else:
        conclusion = (
            f"No se rechaza la normalidad de los residuos (p-valor = {p_valor:.4g} >= "
            f"alfa = {alfa:.4g}); esto no demuestra que sean normales."
        )
    return estadistico, p_valor, conclusion


def prueba_levene(
    df: pd.DataFrame,
    col_trat: str,
    col_resp: str,
    alfa: float = 0.05,
) -> tuple[float, float, str]:
    """Evalúa la igualdad de varianzas entre tratamientos con Levene.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna con la respuesta numérica.
        alfa: Nivel de significancia entre cero y uno.

    Returns:
        Estadístico de Levene, p-valor y conclusión en español.

    Raises:
        ValueError: Si alfa no es válido o los datos no cumplen los requisitos del DCA.
    """
    if not 0 < alfa < 1:
        raise ValueError("Alfa debe estar entre cero y uno.")
    errores = validar_dca(df, col_trat, col_resp)
    if errores:
        raise ValueError(" ".join(errores))

    grupos = [
        grupo[col_resp].to_numpy(dtype=float)
        for _, grupo in df.groupby(col_trat, observed=True, sort=False)
    ]
    # Levene usa Z_ij = |Y_ij - mediana_i| (center='median') para contrastar varianzas iguales.
    resultado = stats.levene(*grupos, center="median")
    estadistico = float(resultado.statistic)
    p_valor = float(resultado.pvalue)
    if p_valor < alfa:
        conclusion = (
            f"Se rechaza la igualdad de varianzas entre tratamientos "
            f"(p-valor = {p_valor:.4g} < alfa = {alfa:.4g})."
        )
    else:
        conclusion = (
            f"No se rechaza la igualdad de varianzas entre tratamientos "
            f"(p-valor = {p_valor:.4g} >= alfa = {alfa:.4g}); esto no demuestra "
            "que las varianzas sean idénticas."
        )
    return estadistico, p_valor, conclusion


def grafico_residuos_vs_ajustados(datos: pd.DataFrame) -> go.Figure:
    """Crea un gráfico de residuos frente a valores ajustados.

    Args:
        datos: DataFrame con columnas ``Ajustados`` y ``Residuos``.

    Returns:
        Gráfico de dispersión con una línea horizontal en cero.

    Raises:
        ValueError: Si faltan las columnas requeridas.
    """
    if not {"Ajustados", "Residuos"}.issubset(datos.columns):
        raise ValueError("Se requieren las columnas 'Ajustados' y 'Residuos'.")

    # Un patrón en e_i frente a y_estimado_i puede revelar varianza no constante o falta de ajuste.
    figura = px.scatter(
        datos,
        x="Ajustados",
        y="Residuos",
        title="Residuos vs. valores ajustados",
        labels={"Ajustados": "Valores ajustados", "Residuos": "Residuos"},
    )
    figura.add_hline(y=0, line_dash="dash", line_color="gray")
    return figura


def grafico_qq(residuos: Sequence[float] | np.ndarray | pd.Series) -> go.Figure:
    """Crea un gráfico Q-Q de los residuos frente a cuantiles normales.

    Args:
        residuos: Residuos del modelo.

    Returns:
        Gráfico Q-Q con una línea de referencia normal.

    Raises:
        ValueError: Si hay menos de tres residuos o algún valor no finito.
    """
    muestra = np.asarray(residuos, dtype=float)
    if muestra.ndim != 1 or not np.isfinite(muestra).all() or muestra.size < 3:
        raise ValueError("El gráfico Q-Q requiere al menos tres residuos finitos.")

    # Si los residuos son normales, sus cuantiles observados se alinean con los cuantiles teóricos.
    (cuantiles_teoricos, residuos_ordenados), (pendiente, intercepto, _) = stats.probplot(
        muestra, dist="norm", fit=True
    )
    datos = pd.DataFrame(
        {
            "Cuantiles teóricos normales": cuantiles_teoricos,
            "Residuos ordenados": residuos_ordenados,
        }
    )
    figura = px.scatter(
        datos,
        x="Cuantiles teóricos normales",
        y="Residuos ordenados",
        title="Gráfico Q-Q de los residuos",
    )
    extremos = [float(np.min(cuantiles_teoricos)), float(np.max(cuantiles_teoricos))]
    figura.add_trace(
        go.Scatter(
            x=extremos,
            y=[pendiente * valor + intercepto for valor in extremos],
            mode="lines",
            name="Referencia normal",
        )
    )
    return figura
