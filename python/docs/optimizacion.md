# Optimización de hiperparámetros y sensibilidad

El proyecto prueba versiones de 10, 100, 200 y 300 correos y adopta
**modelo_clasificador_300.pkl como modelo final**. Las tres versiones menores
se conservan para comparación; las métricas por versión se detallan en la evaluación actual.

Estado actual: 26 de octubre de 2026. Fuentes: grid_search.csv, model_comparison.csv,
sensitivity.json y training_summary.json, dentro de results/metrics.

## Diseño del experimento

La búsqueda usa los **280 correos** de la etapa de selección. No consulta las
respuestas de los 20 diagnósticos para elegir ajustes. Se utiliza F1 macro con
cuatro folds estratificados, barajados con semilla 42. El TF-IDF se aprende
dentro de cada fold externo. La calibración SVM tiene dos folds internos y
reutiliza el vocabulario del train externo, limitación que debe declararse.

Los 20 originales ya se revisaron durante el desarrollo; por eso se reportan
como diagnóstico y no como una evaluación ciega de todas las decisiones.
Los 25 sin etiquetas tampoco se emplean en la búsqueda. Su contenido sí se
discutió para orientar refuerzos, así que ahora son ejemplos de regresión.

## Grilla explorada

| Hiperparámetro | Valores | Qué cambia |
|---|---|---|
| C | 0.1, 1.0, 10.0 | Intensidad de regularización del clasificador |
| class_weight | None, balanced | Peso asignado a clases durante el ajuste |
| min_df | 1, 2 | Frecuencia documental mínima para conservar un término |

ngram_range=(1,2) permanece fijo. Son 12 combinaciones de LR y 12 de SVM:
24 configuraciones y 96 ajustes externos de CV, además de los ajustes internos
del calibrador y del refit. Se guarda la grilla completa con medias, desviaciones,
puntuaciones de train, tiempos y ranking. La versión ejecutada de GridSearchCV
se consulta en la [documentación oficial](https://scikit-learn.org/1.5/modules/generated/sklearn.model_selection.GridSearchCV.html).

## Antes y después

| Modelo | F1 macro CV | Desviación CV | F1 train CV |
|---|---:|---:|---:|
| baseline | 0.1122 | 0.0019 | 0.1122 |
| logistic | 0.9373 | 0.0160 | 1.0000 |
| svm | 0.9617 | 0.0185 | 1.0000 |
| logistic_optimized | 0.9649 | 0.0211 | 1.0000 |
| svm_optimized | 0.9650 | 0.0161 | 1.0000 |

La SVM pasa de 0.961725 a 0.965000:
mejora absoluta de **0.003275**, aproximadamente
**0.328 puntos porcentuales** de F1.
No se presenta como un aumento grande. LR ajustada queda muy cerca; se necesitan
más datos y un diseño de evaluación más fuerte para afirmar una ventaja real.

Configuración final: `{"classifier__estimator__C": 10.0, "classifier__estimator__class_weight": null, "tfidf__min_df": 1}`. La mejor configuración puntual no tiene por
qué coincidir con el mejor promedio marginal de un solo hiperparámetro.

## Ranking de sensibilidad

La sensibilidad se calcula como la diferencia entre el mayor y menor F1 CV
medio por nivel de un hiperparámetro, promediando los otros factores en la
grilla de la familia seleccionada. No es importancia causal ni significancia.

| Puesto | Hiperparámetro | Amplitud de medias marginales |
|---:|---|---:|
| 1 | classifier__C | 0.005065 |
| 2 | tfidf__min_df | 0.005011 |
| 3 | classifier__class_weight | 0.001145 |

### C: regularización

![Efecto marginal de C](../documentacion/imagenes/sensitivity_classifier__C.png)

El cambio de C tiene la mayor amplitud, aunque es pequeña en esta grilla.
El promedio marginal favorece C=1, mientras el mejor punto conjunto utiliza
C=10, min_df=1 y sin pesos de clase. No hay contradicción: uno promedia y el
otro elige una combinación completa.

### Frecuencia mínima de términos

![Efecto marginal de min_df](../documentacion/imagenes/sensitivity_tfidf__min_df.png)

min_df=1 conserva vocabulario infrecuente que puede describir incidentes poco
representados. En datos reales también podría retener ruido o identificadores;
no se supone que siempre vaya a resultar mejor.

### Pesos de clase

![Efecto marginal de pesos](../documentacion/imagenes/sensitivity_classifier__class_weight.png)

La amplitud es la menor. El corpus actual tiene un desbalance moderado y la
mejor combinación puntual no usa balanced. Esto no demuestra equidad entre
grupos de personas ni elimina el riesgo de fallos en categorías minoritarias.

## Dependencia parcial e interacciones: Workshop S5

Los gráficos anteriores son medias marginales empíricas de la grilla. Se
conservan como descripción directa de resultados. Además se implementó el
procedimiento del Workshop S5 con un **modelo sustituto RandomForestRegressor**
y `PartialDependenceDisplay`, en `src/optimization_analysis.py`.

El sustituto aprende las 12 configuraciones SVM ya medidas y su F1 macro CV.
Entradas: log10(C), class_weight codificado None=0/balanced=1 y min_df. Se usan
300 árboles, max_depth=3 y semilla 42. No se incorpora como clasificador de
tickets, no se guarda otro .pkl y no se modifican los cuatro modelos existentes.

```cmd
python -m src.optimization_analysis
```

También se integra en `src.train` para futuros experimentos y en el notebook
04, ejecutado con los gráficos y resultados actuales.

![PDP de los tres hiperparámetros sobre el sustituto](../documentacion/imagenes/s5_pdp_hiperparametros.png)

Los PDP estiman cómo cambia el rendimiento al variar un hiperparámetro,
promediando los demás. El eje C representa 0.1/1/10 en escala logarítmica;
class_weight solo admite los dos extremos y min_df los valores 1/2. Las líneas
entre esos valores son una ayuda visual, no nuevos experimentos observados.
No son PDP de palabras ni explicaciones de un ticket individual.

![Interacción entre C y min_df mediante PDP bidimensional](../documentacion/imagenes/s5_pdp_interaccion.png)

La interacción bidimensional complementa la matriz de medias de la grilla:

![Medias observadas de C y min_df](../documentacion/imagenes/hyperparameter_interaction.png)

### Importancia de hiperparámetros del sustituto

Se registran dos medidas: importancia por reducción de impureza (MDI) del bosque
y aumento del MAE al permutar una columna. La permutación se calcula sobre las
configuraciones ajustadas: es exploratoria, no una evaluación independiente.

| Orden por permutación | Hiperparámetro | Aumento medio de MAE | Importancia MDI |
|---:|---|---:|---:|
| 1 | min_df | 0.002172 | 0.4035 |
| 2 | log10_C | 0.002160 | 0.5396 |
| 3 | class_weight_balanced | 0.000206 | 0.0568 |

![Importancia por permutación sobre las configuraciones](../documentacion/imagenes/s5_importancia_hiperparametros.png)

C y min_df concentran el efecto; su orden cambia según la medida y sus valores
por permutación están prácticamente empatados. class_weight tiene menor efecto.
El ranking marginal previo pone C ligeramente primero y no se sustituye por
este ranking como si fueran la misma medida. No se calcula fANOVA ni se afirma
importancia causal.

### Calidad y límites del sustituto

Leave-one-out sobre las 12 configuraciones: MAE **0.002389** y R²
**0.4712**. El F1 observado va de 0.9510 a
0.9650. La aproximación tiene error apreciable frente a ese rango:
las curvas no justifican conclusiones finas ni extrapolación fuera de la grilla.

Los valores completos están en `results/metrics/s5_surrogate_analysis.json` y
`s5_hyperparameter_importance.csv`. No son métricas de generalización del
clasificador. La mejora real antes/después sigue siendo 0.003275 de F1 CV
(0.328 puntos porcentuales); generar PDP no aumentó ese rendimiento.

## Comparación de los cuatro tamaños

Los modelos 10/100/200/300 usan los ajustes seleccionados, con vocabularios y
clasificadores aprendidos desde cero para cada subconjunto. Comparten registros
de forma intencional. No se optimiza cada uno por separado, para reducir la
mezcla de efectos de tamaño y configuración. Sin embargo, los ajustes se
eligieron con el conjunto mayor y el origen sintético también cambia entre
registros; no es una curva de aprendizaje que aísle todas las variables.

No se ha medido accuracy de los cuatro sobre una prueba común nueva etiquetada.
Más confianza en los 25 no equivale a más aciertos. La prueba por consola está
preparada para observar categorías, confianza y dudas sin usar respuestas ocultas.

## Sobreajuste y siguientes controles

F1 de resustitución en los propios datos finales: 1.0000.
F1 CV de la etapa de 280: 0.9650. F1 del diagnóstico de
20: 0.9511. Son poblaciones y fases distintas, no tres pruebas
independientes del mismo modelo final. La diferencia train/CV advierte que
no se puede asegurar ausencia de sobreajuste.

La búsqueda introduce sesgo de selección sobre la CV y el estilo sintético
puede facilitar el resultado. Para el siguiente experimento conviene una prueba
real, independiente y etiquetada por otra persona, con división por conversación
o plantilla; luego nested CV o una evaluación temporal si el tamaño lo permite.
No cambiar una etiqueta de test para favorecer una predicción ni repetir ajustes
hasta acertar los 25 y después llamarlos datos no vistos.

## Comprobación posterior por tamaño

| Correos | F1 en entrenamiento | F1 macro CV | Accuracy CV | F1 baseline CV | Revisar de 25 |
|---:|---:|---:|---:|---:|---:|
| 10 | 0.5000 | No viable | No viable | No viable | 22 |
| 100 | 1.0000 | 0.9201 | 0.9200 | 0.0968 | 2 |
| 200 | 1.0000 | 0.9442 | 0.9450 | 0.0968 | 1 |
| 300 | 1.0000 | 0.9543 | 0.9533 | 0.1154 | 2 |

La CV por tamaño es exploratoria y no vuelve a optimizar hiperparámetros.
No sustituye la mejora antes/después del Workshop S5 ni utiliza los 25 sin
etiquetas para escoger ajustes. No es posible calcular la misma CV para 10
con la calibración interna actual.
