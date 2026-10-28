# Optimización de hiperparámetros

## 1. Proceso de optimización de hiperparámetros (del Workshop S5)

Se compararon pipelines **TF-IDF + regresión logística** y **TF-IDF + SVM calibrada** con `GridSearchCV`, usando **F1 macro**. La búsqueda empleó **280 correos**, **4 particiones estratificadas** y **semilla 42**. TF-IDF se ajustó en cada partición de entrenamiento; la calibración sigmoide de SVM usó **2 particiones internas**.

Se probaron **12 combinaciones por familia: 24 configuraciones y 96 ajustes externos**, además de calibración y reajuste. Los 20 correos reservados se usaron como diagnóstico, no para puntuar la grilla, y ya se habían revisado durante el desarrollo. Los 25 casos funcionales no se usaron para elegir parámetros.

Para el **Workshop S5** se ajustó un sustituto `RandomForestRegressor` a las **12 configuraciones SVM** y sus resultados: **300 árboles, profundidad 3 y semilla 42**. Este modelo permite analizar PDP, importancia e interacciones; no clasifica tickets ni cambia los modelos guardados.

Código: [búsqueda](../src/train.py), [análisis S5](../src/optimization_analysis.py) y [notebook](../notebooks/04_optimizacion.ipynb). Para repetir el análisis guardado, desde `python/`:

```bash
python -m src.optimization_analysis
```

## 2. Hiperparámetros explorados y rangos

| Hiperparámetro | Valores explorados | Función |
|---|---|---|
| `C` | `0.1`, `1.0`, `10.0` | Controla la regularización del clasificador |
| `class_weight` | `None`, `balanced` | Define si se ponderan las clases durante el ajuste |
| `min_df` | `1`, `2` | Frecuencia documental mínima para conservar un término |

La grilla está en [config.yaml](../config.yaml) y sus resultados en [grid_search.csv](../results/metrics/grid_search.csv). Se mantuvieron fijos los unigramas/bigramas, la frecuencia sublineal, la normalización de acentos y `max_df=1.0`.

## 3. Resultados del análisis de sensibilidad

La sensibilidad es la diferencia entre el mayor y menor **F1 medio de cada valor**, promediando las demás combinaciones SVM.

| Hiperparámetro | Medias marginales de F1 macro CV | Amplitud |
|---|---|---:|
| `C` | 0.1: **0.956399**; 1: **0.961463**; 10: **0.961361** | 0.005065 |
| `min_df` | 1: **0.962246**; 2: **0.957235** | 0.005011 |
| `class_weight` | None: **0.959169**; balanced: **0.960313** | 0.001145 |

**C y min_df tienen mayor efecto; class_weight, menor.** El promedio marginal favorece `C=1`, pero la mejor combinación usa `C=10`: promediar valores no equivale a elegir una configuración completa.

![Sensibilidad de C](../documentacion/imagenes/sensitivity_classifier__C.png)

![Sensibilidad de min_df](../documentacion/imagenes/sensitivity_tfidf__min_df.png)

![Sensibilidad de class_weight](../documentacion/imagenes/sensitivity_classifier__class_weight.png)

Fuente: [sensitivity.json](../results/metrics/sensitivity.json). Estas amplitudes describen la grilla; no demuestran causalidad ni significancia estadística.

## 4. Partial dependence plots

Los PDP usan `PartialDependenceDisplay` sobre el sustituto. Muestran el **F1 macro CV estimado** al cambiar un parámetro y promediar los demás.

![PDP de los hiperparámetros](../documentacion/imagenes/s5_pdp_hiperparametros.png)

Las entradas son `log10(C)`, `class_weight` (None=0, balanced=1) y `min_df`. Las líneas entre valores discretos no son nuevos experimentos. Los gráficos explican el rendimiento estimado, no la predicción de un correo.

El sustituto obtuvo **MAE = 0.002389 y R² = 0.4712** en leave-one-out, con F1 observado entre **0.9510 y 0.9650**. Es una aproximación exploratoria; no permite extrapolar fuera de la grilla. Ver [reporte](../results/metrics/s5_surrogate_analysis.json).

## 5. Ranking de importancia de hiperparámetros

El ranking mide cuánto **aumenta el MAE al permutar una variable**, con **40 repeticiones**. También se incluye la importancia por reducción de impureza del bosque (MDI).

| Puesto por permutación | Hiperparámetro | Aumento medio de MAE | Importancia MDI |
|---:|---|---:|---:|
| 1 | `min_df` | 0.002172 | 0.4035 |
| 2 | `log10_C` | 0.002160 | 0.5396 |
| 3 | `class_weight_balanced` | 0.000206 | 0.0568 |

![Ranking de importancia por permutación](../documentacion/imagenes/s5_importancia_hiperparametros.png)

**min_df y C están casi empatados por permutación**; MDI sitúa C primero. Son medidas distintas y pueden dar órdenes diferentes. La permutación usa las 12 configuraciones ajustadas, sin una muestra independiente; no demuestra causalidad.

Fuente: [s5_hyperparameter_importance.csv](../results/metrics/s5_hyperparameter_importance.csv).

## 6. Análisis de interacciones

Se estudió **C × min_df** con un PDP bidimensional y las medias observadas en la grilla.

![PDP bidimensional de C y min_df](../documentacion/imagenes/s5_pdp_interaccion.png)

![Interacción observada de C y min_df](../documentacion/imagenes/hyperparameter_interaction.png)

| C | F1 macro CV medio con min_df=1 | F1 macro CV medio con min_df=2 |
|---:|---:|---:|
| 0.1 | 0.960015 | 0.952783 |
| 1.0 | 0.961725 | 0.961202 |
| 10.0 | 0.965000 | 0.957722 |

Cada media reúne las dos opciones de `class_weight`. La diferencia entre valores de `min_df` es pequeña con `C=1` y mayor con `C=0.1` o `10`. La mejor media es `C=10, min_df=1`. El resultado describe esta grilla, no garantiza el mismo comportamiento con datos reales.

## 7. Configuración final seleccionada y justificación

| Componente | Valor seleccionado |
|---|---|
| Clasificador | SVM lineal con calibración sigmoide |
| `C` | `10.0` |
| `class_weight` | `None` (`null` en YAML) |
| `min_df` | `1` |
| `ngram_range` | `[1, 2]` |
| Particiones de calibración | `2` |
| Semilla | `42` |

La configuración obtuvo **F1 macro CV de 0.965000**, frente a **0.964939** de regresión logística optimizada. `min_df=1` conserva términos infrecuentes; `C=10` reduce la regularización frente a los valores menores y `class_weight=None` no pondera las clases. Se eligió la combinación completa, no cada valor por separado.

Los valores están en [config.yaml](../config.yaml) y [training_summary.json](../results/metrics/training_summary.json). Después se entrenó con **300 correos**. Las versiones de **10, 100, 200 y 300** usan estos parámetros sin repetir la búsqueda. La pequeña ventaja sobre regresión logística no prueba superioridad en producción.

## 8. Comparación antes/después de la optimización

Comparación registrada sobre los **280 correos de la etapa de selección**, con el mismo esquema de validación cruzada:

| Modelo | F1 macro CV antes | F1 macro CV después | Mejora absoluta |
|---|---:|---:|---:|
| Regresión logística | 0.937289 | 0.964939 | +0.027650 |
| SVM calibrada | 0.961725 | 0.965000 | +0.003275 |

La mejora de SVM es de **0.328 puntos porcentuales de F1 macro**. Su desviación entre particiones baja de **0.018527 a 0.016136**. El baseline obtiene **0.112179**. Ver [model_comparison.csv](../results/metrics/model_comparison.csv).

La selección sobre la misma validación puede dar resultados optimistas. Generar PDP no mejora por sí solo el clasificador. Estas cifras corresponden a la optimización sobre 280 correos; la evaluación posterior del modelo de 300 registra **accuracy CV de 0.9533 y F1 macro CV de 0.9543** en [version_evaluation.json](../results/metrics/version_evaluation.json).