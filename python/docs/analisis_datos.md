# Análisis de datos

## 1. Descripción detallada del dataset

La fuente son **cuatro conjuntos de 10, 100, 200 y 300 correos simulados en español**, creados para entrenar y comparar clasificadores de soporte TI. El [corpus maestro](../data/raw/correos.json) contiene los 300 registros; las [muestras de entrenamiento](../data/train/) son anidadas y se seleccionaron con semilla 42. No representan una muestra aleatoria de correos reales de una organización.

| Variable | Tipo y contenido | Uso |
|---|---|---|
| `titulo` | Texto del asunto | Entrada del modelo |
| `cuerpo` | Texto de la solicitud | Entrada del modelo |
| `clasificacion` | Accesos, aplicaciones, infraestructura u otros | Etiqueta de entrenamiento y evaluación |
| `texto` | Título y cuerpo normalizados y concatenados; variable derivada | Representación utilizada para calcular TF-IDF |

La etiqueta nunca se incorpora al texto de entrada. Las categorías distinguen problemas de identidad/permisos (**accesos**), funcionamiento del software (**aplicaciones**), equipos/red/servicios base (**infraestructura**) y orientación, capacitación u otras solicitudes (**otros**). La causa descrita importa más que mencionar una aplicación: pedir capacitación sobre JDE puede corresponder a otros.

Los [25 correos de prueba](../data/test/correos_test_25.json) contienen título y cuerpo y no se usan para entrenar. Sirven para pruebas funcionales y revisión manual; su contenido permite reconocer el tipo de solicitud sin necesitar etiquetas para ejecutarlos. Calcular accuracy o F1 exigiría registrar categorías esperadas validadas. Son casos conocidos del desarrollo, no una evaluación externa independiente.

No se ha declarado una licencia específica de los datos. La [licencia MIT del código](../LICENSE) no se extiende automáticamente al dataset.

## 2. Estadísticas descriptivas

### Tamaño y distribución por categoría

| Conjunto | Accesos | Aplicaciones | Infraestructura | Otros | Total |
|---|---:|---:|---:|---:|---:|
| 10 correos | 3 | 3 | 2 | 2 | 10 |
| 100 correos | 25 | 25 | 25 | 25 | 100 |
| 200 correos | 50 | 50 | 50 | 50 | 200 |
| 300 correos | 70 | 90 | 70 | 70 | 300 |

En el conjunto de 300, aplicaciones representa **30,00 %** y cada categoría restante **23,33 %**. La razón entre la clase mayor y una menor es **90/70 = 1,29**. Los conjuntos de 100 y 200 están balanceados; el de 10 contiene solo dos ejemplos en dos de sus clases.

### Longitudes y calidad del corpus de 300 correos

Las siguientes cifras corresponden al **texto limpio combinado**, según [eda.json](../results/metrics/eda.json):

| Estadística | Caracteres | Palabras |
|---|---:|---:|
| Media | 409,26 | 63,84 |
| Mediana | 350 | 55 |
| Desviación estándar muestral | 112,72 | 18,55 |
| Mínimo | 279 | 42 |
| Primer cuartil | 320 | 49 |
| Tercer cuartil | 532 | 85 |
| Máximo | 643 | 100 |

Se cargaron **300 registros únicos**, con **0 valores faltantes** en los campos obligatorios. La correlación entre caracteres y palabras es **0,9788**. Se identificaron **0 outliers superiores de longitud** usando el criterio de 1,5 veces el rango intercuartílico.

## 3. Visualizaciones del EDA (mínimo 5-6 gráficos relevantes)

Los seis gráficos se generan mediante la función de EDA de [src/train.py](../src/train.py).

### Gráfico 1. Distribución de categorías

![Distribución de categorías](../documentacion/imagenes/01_class_distribution.png)

Permite comprobar el desbalance moderado: 90 aplicaciones frente a 70 ejemplos de cada categoría restante. Estas proporciones pertenecen al corpus simulado y no representan frecuencias reales de incidentes.

### Gráfico 2. Distribución de longitud del texto

![Distribución de caracteres del texto limpio](../documentacion/imagenes/02_text_lengths.png)

Muestra la variación entre textos de 279 y 643 caracteres. Permite detectar concentraciones de longitudes y posibles diferencias de estilo entre ejemplos.

### Gráfico 3. Cantidad de palabras por categoría

![Palabras por categoría](../documentacion/imagenes/03_words_by_class.png)

El diagrama de cajas compara medianas, dispersión y valores extremos por clase. Ayuda a revisar si la longitud puede actuar como una pista de estilo en lugar de representar el problema técnico.

### Gráfico 4. Relación entre longitud del título y del cuerpo

![Longitud del título frente a longitud del cuerpo](../documentacion/imagenes/04_title_body.png)

Compara los tamaños de los campos originales para observar su variación y complementariedad. Justifica conservar ambos como entrada en lugar de depender solo del asunto.

### Gráfico 5. Términos frecuentes

![Frecuencia de términos del corpus](../documentacion/imagenes/05_common_terms.png)

Presenta las 18 palabras más frecuentes, incluidas palabras funcionales. Permite identificar vocabulario repetido y revisar posibles plantillas; la frecuencia por sí sola no demuestra capacidad predictiva.

### Gráfico 6. Correlaciones de longitud

![Correlaciones entre caracteres, palabras y longitud del título](../documentacion/imagenes/06_length_correlations.png)

La matriz resume relaciones entre medidas de tamaño del texto. La alta correlación caracteres-palabras describe el corpus; no implica causalidad ni una relación entre causas de incidentes.

## 4. Identificación de patrones, correlaciones, outliers

| Aspecto | Hallazgo | Interpretación y decisión |
|---|---|---|
| Distribución de clases | Aplicaciones tiene 90 registros; las demás, 70 | Desbalance moderado; observar F1 macro y resultados por categoría |
| Estilo y vocabulario | Textos simulados en español con expresiones repetidas | Posible aprendizaje de plantillas; no asumir generalización a otros idiomas o empresas |
| Términos asociados | El reporte de entrenamiento incluye «referencia omitida» entre términos asociados a aplicaciones | Posible pista espuria; requiere revisión, sin atribuirle influencia causal demostrada |
| Correlación | Caracteres y palabras: **0,9788** | Ambas medidas describen tamaño; no se incorporan como variables numéricas adicionales al clasificador |
| Outliers de longitud | Q1=320, Q3=532 e IQR=212; límite superior **850 caracteres**; máximo observado 643 | No hay registros por encima de Q3 + 1,5×IQR; no se eliminan correos por este criterio |
| Similitud entre conjuntos | Las muestras de 10, 100 y 200 están contenidas en la de 300 | Las comparaciones comparten registros y no son pruebas independientes |

La ausencia de outliers por longitud no descarta anomalías semánticas, etiquetas discutibles o solicitudes con varias causas. No se calculan correlaciones numéricas arbitrarias entre las categorías, porque son etiquetas nominales. Los términos asociados se registran en [training_summary.json](../results/metrics/training_summary.json).

## 5. Decisiones de preprocesamiento justificadas

| Decisión | Implementación | Justificación |
|---|---|---|
| Validar estructura y contenido | Exigir los campos obligatorios, textos útiles y etiquetas permitidas; máximo de 20.000 caracteres por campo de entrada | Evitar entradas inválidas y errores silenciosos |
| Normalizar escritura | Decodificar entidades HTML, aplicar Unicode NFKC, minúsculas, retirar etiquetas HTML, puntuación y espacios repetidos | Reducir variantes que no aportan al tipo de incidente |
| Sustituir identificadores | Reemplazar correos, URLs, IPv4, nombres de archivos y números largos por términos genéricos | Reducir vocabulario irrelevante y pistas artificiales; no equivale a anonimización completa |
| Combinar título y cuerpo | Concatenar ambos una sola vez | Conservar el resumen breve del asunto y el contexto de la solicitud |
| Controlar duplicados y conflictos | Eliminar textos normalizados duplicados antes de dividir; detener la carga si tienen etiquetas contradictorias | Evitar repetición entre particiones y supervisión inconsistente |
| Conservar negaciones | No utilizar una lista genérica de stopwords | Mantener expresiones como «no puedo acceder», relevantes para interpretar la solicitud |
| Representar con TF-IDF | Unigramas y bigramas, frecuencia sublineal, normalización de acentos y L2 | Capturar términos y expresiones cortas con una representación dispersa adecuada para SVM lineal |
| Ajustar vocabulario en entrenamiento | Aprender TF-IDF dentro de cada partición externa de validación | Evitar aprender vocabulario de la partición externa de evaluación |

Implementación: [data_processing.py](../src/data_processing.py) y [model.py](../src/model.py). La calibración interna de SVM reutiliza el vocabulario del entrenamiento externo; no se ajusta otro vocabulario por subpartición de calibración.

En el flujo operativo, el nodo de código **Limpiar firma y datos** de n8n añade limpieza de firmas y redacción de datos sensibles antes de enviar el asunto/cuerpo a NexpAPI y OpenAI. Este paso no modifica los datasets de entrenamiento ni anonimiza los adjuntos.

## 6. Manejo de datos faltantes o desbalanceados

### Datos faltantes e inválidos

El corpus cargado tiene **cero campos obligatorios faltantes**. El cargador rechaza campos ausentes, nulos, no textuales, vacíos, sin letras, demasiado largos o etiquetas fuera de las cuatro categorías. No se imputan textos ni se inventan etiquetas: el registro debe corregirse en origen antes de entrenar. Si un texto duplicado presenta etiquetas contradictorias, la carga se detiene para revisión.

### Datos desbalanceados

Se conserva la distribución del conjunto de 300 y se utilizan particiones estratificadas y **F1 macro**, que da el mismo peso a cada categoría, además de métricas por clase. La optimización comparó `class_weight=None` y `balanced`; la combinación seleccionada usa **`None`**, según [config.yaml](../config.yaml) y la [optimización](optimizacion.md).

No se aplican sobremuestreo, submuestreo ni generación de registros durante el ajuste. Los conjuntos de 100 y 200 se seleccionaron balanceados por clase; esto es una decisión de construcción de muestras, no una técnica de reequilibrio aplicada al conjunto completo durante el entrenamiento. La muestra de 10 es demostrativa y sus clases con solo dos registros limitan la evaluación con calibración interna.
