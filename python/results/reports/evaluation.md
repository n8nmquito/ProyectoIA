# Informe de ejecución

Resultados medidos; no estimaciones de producción.

Train: 280; test: 20; clases: {'aplicaciones': 90, 'accesos': 70, 'infraestructura': 70, 'otros': 70}.
Modelo final: 300 correos. Modelo de evaluación: 280 correos.
Las métricas de test corresponden al modelo de evaluación. Si el modelo final usa todo el corpus, no tiene test independiente.
F1 macro CV antes: 0.9617; después: 0.9650.
Cambio absoluto de F1 CV: 0.0033.
Accuracy test: 0.9500; F1 macro test: 0.9511.
Baseline test F1 macro: 0.1552.
F1 train: 1.0000. Una brecha train/CV/test sugiere sobreajuste.
Parámetros: `{"classifier__estimator__C": 10.0, "classifier__estimator__class_weight": null, "tfidf__min_df": 1}`.

## Sensibilidad (amplitud de medias marginales; no causal)

- param_classifier__C: 0.0051
- param_tfidf__min_df: 0.0050
- param_classifier__class_weight: 0.0011

## Alcance de evaluación

El test original ya se examinó durante el desarrollo. Se conserva fuera de entrenamiento como referencia diagnóstica; no es una validación nueva independiente de la ampliación.

## Errores de test

- Fila 7: real accesos; predicha aplicaciones; confianza 0.619. Consultar el texto local en test.csv; revisar ambigüedad y vocabulario.