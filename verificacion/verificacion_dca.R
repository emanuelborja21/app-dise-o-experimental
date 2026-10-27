# Lee los datos preparados para la verificación; ejecuta este script desde la carpeta verificacion.
datos <- read.csv("../data/dca_mi_variante.csv") # Importa las observaciones para comprobar el análisis de forma independiente.

# Ajusta el modelo de un DCA, donde factor(secador) compara las medias de humedad de los secadores.
modelo <- aov(humedad ~ factor(secador), data = datos) # Separa la variación atribuible a secadores de la variación residual.

# Muestra la tabla de análisis de varianza para evaluar si hay evidencia de diferencias entre medias.
print(summary(modelo)) # Reporta los grados de libertad, cuadrados medios, estadístico F y valor p calculados por R.

# Calcula la media observada de humedad para cada secador y facilita la comparación descriptiva.
medias_por_secador <- aggregate(humedad ~ secador, data = datos, FUN = mean) # Agrupa las réplicas por secador y promedia su respuesta.

# Imprime las medias calculadas con las observaciones, sin escribir valores de ejemplo.
print(medias_por_secador) # Permite contrastar la tendencia de cada secador con los resultados del ANOVA.

# Extrae la tabla ANOVA para obtener el cuadrado medio del error usado en el CV.
tabla_anova <- summary(modelo)[[1]] # Conserva las cantidades calculadas por el modelo ajustado.

# Toma el cuadrado medio residual, que estima la variación aleatoria entre réplicas del mismo tratamiento.
cuadrado_medio_error <- tabla_anova["Residuals", "Mean Sq"] # El renglón Residuals representa el error experimental.

# Calcula la media general de humedad como referencia para expresar el error en escala relativa.
media_general <- mean(datos$humedad) # Usa todas las observaciones disponibles en el archivo.

# Calcula CV = sqrt(CME) / media general * 100 para expresar el error experimental como porcentaje.
coeficiente_variacion <- sqrt(cuadrado_medio_error) / media_general * 100 # Relaciona el error típico con el nivel promedio de humedad.

# Imprime el CV calculado para comparar la precisión experimental con la salida de la aplicación.
cat(sprintf("Coeficiente de variación: %.4f%%\n", coeficiente_variacion)) # Formatea solo el resultado obtenido de los datos.

# Aplica Tukey para comparar pares de medias después del ANOVA.
resultado_tukey <- TukeyHSD(modelo) # Ajusta las comparaciones por multiplicidad para controlar el error familiar.

# Imprime las diferencias por pares, sus intervalos y los valores p ajustados calculados por R.
print(resultado_tukey) # Ayuda a verificar qué medias de secadores difieren según el procedimiento de Tukey.