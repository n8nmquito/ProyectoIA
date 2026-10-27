# Análisis de los datos

El proyecto prueba versiones de 10, 100, 200 y 300 correos y adopta
**modelo_clasificador_300.pkl como modelo final**. Las tres versiones menores
se conservan para comparación; las métricas por versión se detallan en la evaluación actual.

Versión documentada: 26 de octubre de 2026. Fuente numérica: `results/metrics/eda.json`.

## Descripción detallada del dataset

El corpus maestro `data/raw/correos.json` contiene 300 correos simulados en
español. Los 100 iniciales fueron suministrados por el usuario y otros 200 se
crearon como ejemplos ficticios para ampliar el corpus. Las ampliaciones
buscaron cubrir categorías y casos funcionales faltantes. No son una muestra
aleatoria de una organización ni tickets reales recopilados de producción.

Cada registro de entrenamiento contiene `titulo`, `cuerpo` y `clasificacion`.
Las únicas etiquetas aceptadas son accesos, aplicaciones, infraestructura y otros.
Título y cuerpo son entradas; clasificación es la respuesta de entrenamiento y
nunca se concatena al texto para predecir.

| Categoría | Criterio de etiquetado | Correos | Porcentaje |
|---|---|---:|---:|
| Accesos | Identidad, cuentas, autenticación, permisos y roles | 70 | 23.33 % |
| Aplicaciones | Errores del programa, cálculos, pantallas y reglas funcionales | 90 | 30.00 % |
| Infraestructura | Equipos, red, almacenamiento y servicios base | 70 | 23.33 % |
| Otros | Orientación, formación, administración y propuestas | 70 | 23.33 % |

Cuando un ticket menciona permisos o conexión, la etiqueta depende de la causa
descrita. Por ejemplo, un permiso realmente ausente se etiqueta accesos; un
programa que calcula mal una condición de visibilidad corresponde a aplicaciones.
La revisión humana sigue siendo necesaria cuando la causa no está clara.

## Datasets exactos por modelo

| Tamaño | Accesos | Aplicaciones | Infraestructura | Otros | Variables TF-IDF aprendidas |
|---:|---:|---:|---:|---:|---:|
| 10 | 3 | 3 | 2 | 2 | 867 |
| 100 | 25 | 25 | 25 | 25 | 6097 |
| 200 | 50 | 50 | 50 | 50 | 10469 |
| 300 | 70 | 90 | 70 | 70 | 14409 |

Los archivos `data/train/correos_10.json`, `correos_100.json`, `correos_200.json`
y `correos_300.json` conservan los registros y el orden usados por su modelo.
Se exportaron desde los índices y huellas guardados en cada `.pkl`, sin sortear
otra muestra. Son conjuntos anidados, seleccionados con semilla 42. Los de
100 y 200 están balanceados; el de 300 conserva la distribución completa.

Para seleccionar ajustes se separaron 280 correos de los 20 originales del
manifiesto de evaluación. Después se ajustó el modelo final con los 300.
Los **25 de `data/test`** solo tienen título y cuerpo y nunca entraron en fit.
No se les atribuye un porcentaje de aciertos, porque ya no hay respuestas de
referencia en ese flujo. Además, se discutieron antes de decidir refuerzos:
sirven como regresión, no como prueba independiente de todo el desarrollo.

## Estadísticas descriptivas

| Medida del texto limpio | Valor |
|---|---:|
| Registros únicos cargados | 300 |
| Campos obligatorios faltantes | 0 |
| Media de caracteres | 409.26 |
| Mediana de caracteres | 350 |
| Mínimo / máximo de caracteres | 279 / 643 |
| Desviación de caracteres | 112.72 |
| Media de palabras | 63.84 |
| Mediana de palabras | 55 |
| Mínimo / máximo de palabras | 42 / 100 |
| Correlación caracteres-palabras | 0.9788 |
| Outliers superiores de longitud con 1.5 IQR | 0 |

La razón entre la clase mayor y las menores es 90/70, aproximadamente 1.29.
No es un desbalance extremo, pero justifica mirar F1 por clase además de accuracy.
La alta correlación entre longitud y cantidad de palabras es esperable y no
implica una relación causal ni demuestra capacidad predictiva.

## Exploración visual: seis gráficos

### 1. Distribución de categorías

![Distribución de las cuatro clases](../documentacion/imagenes/01_class_distribution.png)

Aplicaciones tiene más ejemplos por el refuerzo de fallos de software. No se
debe presentar esa proporción como frecuencia real de incidentes de una empresa.

### 2. Longitud del texto limpio

![Distribución de caracteres](../documentacion/imagenes/02_text_lengths.png)

La longitud varía entre ejemplos iniciales y ampliaciones. Esa diferencia puede
introducir pistas de estilo relacionadas con el origen sintético de los textos.

### 3. Cantidad de palabras por clase

![Palabras por categoría](../documentacion/imagenes/03_words_by_class.png)

Permite revisar si una categoría se está distinguiendo por textos más largos
en lugar de por el problema técnico. No se recortaron registros por esa razón.

### 4. Longitudes del título y del cuerpo

![Relación entre título y cuerpo](../documentacion/imagenes/04_title_body.png)

Combinar los dos campos evita perder la descripción breve del título o el
contexto del cuerpo. Actualmente ambos se concatenan una sola vez, sin pesos distintos.

### 5. Términos frecuentes

![Frecuencias de términos](../documentacion/imagenes/05_common_terms.png)

El gráfico incluye palabras funcionales. Se decidió no usar una lista genérica
de stopwords para conservar negaciones y expresiones relevantes. TF-IDF reduce
el peso relativo de términos muy comunes, aunque no entiende su significado.

### 6. Correlaciones de longitud

![Correlaciones descriptivas](../documentacion/imagenes/06_length_correlations.png)

Son relaciones entre medidas de tamaño del texto, no correlaciones entre
causas de incidentes. Se utilizan para conocer el corpus, no para afirmar causalidad.

## Decisiones de preprocesamiento y control de calidad

Se aplica Unicode NFKC, minúsculas, eliminación de etiquetas HTML y normalización
de espacios. Algunas direcciones de correo, URLs, IP, números largos y nombres
de archivos se sustituyen por términos genéricos. Esto reduce identificadores
y pistas artificiales, pero no garantiza eliminar nombres, secretos o información
personal escrita de otra forma.

Se rechazan campos ausentes, nulos, no textuales, vacíos, con solo símbolos o
números, etiquetas fuera del conjunto permitido y campos de más de 20.000
caracteres. Los duplicados normalizados se eliminan antes de dividir; si un mismo
texto tiene etiquetas contradictorias se detiene la carga. No se inventan
etiquetas faltantes ni se imputan automáticamente.

### Manejo de datos faltantes y desbalanceados

Los campos obligatorios faltantes se rechazan para evitar construir entradas
incompletas o etiquetas supuestas. El corpus cargado registra cero faltantes.
No se aplican imputación, sobremuestreo ni generación adicional durante el fit.
Se comparó `class_weight=None` con `balanced`; la configuración seleccionada
usa `None`. Se conservan la distribución original de 300, las particiones
estratificadas y F1 macro para observar el rendimiento entre categorías.

### Justificación de las transformaciones

Concatenar título y cuerpo conserva la descripción breve y el contexto del
incidente. La normalización reduce variantes de escritura y el reemplazo de
identificadores limita vocabulario irrelevante, sin garantizar anonimización.
No se eliminan stopwords genéricas para conservar negaciones. TF-IDF con
unigramas y bigramas representa términos y expresiones cortas sin requerir
GPU; su vocabulario se aprende solo en el entrenamiento de cada fold externo.

El vocabulario TF-IDF se aprende dentro del fold externo de entrenamiento.
La calibración interna de SVM reutiliza el TF-IDF de ese train externo; no tiene
un vocabulario independiente para cada subfold de calibración. Esto debe revisarse
si se pretende una auditoría estricta de calibración con datos reales.

## Sesgos y límites del dataset

Los textos comparten idioma, dominio y parte del estilo de generación. No hay
atributos demográficos para medir fairness poblacional. Los marcadores como
«referencia omitida» aparecen entre términos asociados a aplicaciones y podrían
actuar como pistas espurias; no se ha demostrado que expliquen un error concreto.
No hay una evaluación independiente por empresa, conversación o plantilla.

La licencia de uso del dataset no se ha especificado por separado. Antes de
usar o publicar correos reales, revisar permisos, anonimización y retención.
Ver [consideraciones éticas](consideraciones_eticas.md).

## Fuente licencia y disponibilidad

El origen es el aporte inicial de 100 correos y la ampliación con 200 ejemplos
ficticios descritos arriba. Por indicación de la responsable del proyecto, se
incluyen el [corpus maestro](../data/raw/correos.json) y los cuatro datasets
de [entrenamiento](../data/train/). La [licencia MIT del código](../LICENSE)
no se extiende automáticamente a los datos. Los modelos, las particiones
procesadas y la hoja de revisión continúan excluidos de Git.
