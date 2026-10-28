# Modelos del clasificador de correos

El modelo final elegido es **modelo_clasificador_300.pkl**.
Los de 10, 100 y 200 se conservan para las pruebas de comparación.

Esta carpeta contiene cuatro versiones del clasificador de tickets de soporte TI.
Cada una aprendió de una cantidad diferente de correos. Las guardamos para
observar cómo cambian las predicciones al darle más ejemplos al sistema.

| Modelo | Correos usados | Su dataset en data/train/ |
|---|---:|---|
| modelo_clasificador_10.pkl | 10 | correos_10.json |
| modelo_clasificador_100.pkl | 100 | correos_100.json |
| modelo_clasificador_200.pkl | 200 | correos_200.json |
| modelo_clasificador_300.pkl | 300 | correos_300.json |

Todos reciben título y cuerpo y sugieren accesos, aplicaciones, infraestructura
u otros. También muestran una confianza estimada; ese porcentaje no garantiza
que la categoría sea correcta. El de 10 es una demostración con muy pocos datos.

Desde CMD en la carpeta del proyecto:

```cmd
python evaluar_nuevos.py --model 100
```

Cambia 100 por 10, 200 o 300 para elegir otra versión. Sin indicar modelo se
utiliza el de 300. Cada versión guarda sus resultados en una carpeta separada.
Los 25 correos de prueba están aparte en data/test y no se usaron para entrenar.

El [README del proyecto](../README.md#8-interfaz-de-usuario) explica la interfaz y sus advertencias.

## Arquitectura y configuración

Los cuatro archivos guardan pipelines TF-IDF con unigramas y bigramas y SVM
lineal calibrada con sigmoide de dos folds. Comparten `C=10`,
`class_weight=None` y `min_df=1`; cada versión aprende su propio vocabulario y
clasificador con los registros de su tamaño. Se conservan índices, huellas y
etiquetas para comprobar el dataset exacto. La selección del modelo de 300 no
equivale a demostrar superioridad en un test externo común a los cuatro.

## Disponibilidad y regeneración

Los `.pkl` siguen excluidos de Git. El corpus y los datasets de entrenamiento
sí se incluyen por indicación de la responsable del proyecto. Solo cargar archivos propios o de
una fuente confiable: pickle puede ejecutar código. Con las copias privadas
del corpus y el manifiesto de particiones, desde `python/`:

```cmd
python -m src.train
python -m src.train_versions
python -m src.export_datasets
```

Estos comandos reemplazan los artefactos de los mismos nombres. Conservar las
versiones anteriores antes de entrenar. La sección de [resultados](../README.md#6-resultados)
documenta las métricas por tamaño y sus límites.

Para verificar los cuatro modelos y repetir las pruebas sin reentrenarlos:

```cmd
python -m src.evaluate_versions
```

El informe distingue entrenamiento, CV exploratoria y predicciones sin
etiquetas. El modelo de 10 tiene muy pocos ejemplos para la CV calibrada.
