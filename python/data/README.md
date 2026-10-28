# Datos del clasificador

El proyecto prueba versiones de 10, 100, 200 y 300 correos y adopta
**modelo_clasificador_300.pkl como modelo final**. Las tres versiones menores
se conservan para comparación; las métricas por versión se detallan en la evaluación actual.

La fuente del proyecto son datasets de **10, 100, 200 y 300 correos
simulados**, con los campos titulo, cuerpo y clasificacion. El archivo
raw/correos.json conserva el corpus maestro de 300. Hay 70 de accesos, 90 de aplicaciones, 70 de
infraestructura y 70 de otros. El título y el cuerpo son las entradas; la
clasificación es la respuesta usada únicamente durante entrenamiento y evaluación.

| Dataset de entrenamiento | Modelo correspondiente | Correos |
|---|---|---:|
| train/correos_10.json | modelo_clasificador_10.pkl | 10 |
| train/correos_100.json | modelo_clasificador_100.pkl | 100 |
| train/correos_200.json | modelo_clasificador_200.pkl | 200 |
| train/correos_300.json | modelo_clasificador_300.pkl | 300 |

Las copias se exportan desde los registros exactos del modelo y mantienen su
orden. Son conjuntos anidados, no cuatro muestras independientes.
`python -m src.export_datasets` permite regenerarlas sin reentrenar.

processed/train.csv contiene los 300 limpios del ajuste final.
processed/evaluation_train.csv y test.csv contienen la etapa diagnóstica 280/20.
[processed/holdout_original.json](processed/holdout_original.json) está incluido en Git e identifica los 20 casos históricos con huellas y etiquetas. No es otro corpus de entrenamiento.

test/correos_test_25.json contiene únicamente titulo y cuerpo. Los 25 no se
usaron en fit; su ejecución solo muestra predicciones y confianza. La carpeta
test no contiene README, etiquetas ni metadatos adicionales.

Los datos son simulados. Por indicación de la responsable del proyecto se
incluyen en Git el [corpus maestro](raw/correos.json) y los cuatro datasets
de [entrenamiento](train/). Los CSV procesados y la hoja de revisión continúan excluidos; el manifiesto de reserva sí está versionado. Los
[modelos entrenados y sus hashes](../models/README.md) están incluidos en Git. La licencia MIT del código no se
extiende automáticamente al dataset. Revisar privacidad y permisos antes de
usar datos reales. Más detalle en [análisis de datos](../docs/analisis_datos.md).

La hoja `evaluation/correos_para_revision.json` reutiliza los mismos 25 correos,
fuera de la carpeta test, con etiquetas vacías. Debe revisarla una persona antes
de calcular métricas con `src.evaluate_reviewed`. Se reportará como regresión
conocida; no como prueba independiente. La hoja se excluye de Git.

La correspondencia exacta entre cada dataset y su archivo de modelo se verifica
con `python -m src.evaluate_versions`. Las huellas y resultados se conservan
en results/metrics/version_evaluation.json.

## Reproducir la partición de diagnóstico

El manifiesto se descarga con el repositorio: no hay que crearlo ni disponer de archivos privados. `config.yaml` lo usa para recuperar los mismos **280 registros de entrenamiento y 20 de diagnóstico**. Los notebooks y `src.train` reconstruyen la división a partir del corpus maestro y las huellas guardadas.

Cuando `holdout_manifest` está definido, esta reserva fija prevalece sobre `test_size`: no se vuelve a sortear el 20 % del corpus actual. El `source_sha256` del manifiesto identifica el corpus histórico con el que se creó; las huellas y etiquetas comprueban que los 20 correos sigan presentes en el corpus ampliado. Si falta uno o cambia su etiqueta, la carga falla en lugar de elegir otro.

El SHA-256 del manifiesto es `c252e2d7daed0bf75f4ad2c67b56ef619f2aadc83df72b8f004c8d762f6e1f0b`, el mismo de [training_summary.json](../results/metrics/training_summary.json). Sus bytes se conservan en Git para no cambiar esa referencia entre Windows y Linux. Los 20 casos ya fueron revisados durante el desarrollo: son un diagnóstico histórico, no una prueba externa ciega.

Para comprobar la reserva sin entrenar ni sobrescribir resultados, desde `python/`:

```bash
python -m pytest tests/test_data_processing.py -q
```

La prueba comprueba el hash, los índices originales, las cuatro categorías y la separación sin solapamientos. Los CSV procesados se generan al ejecutar `python -m src.train`; ese comando también reentrena y reemplaza el modelo final y sus reportes, por lo que conviene guardar una copia antes de usarlo.