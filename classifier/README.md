# Segunda técnica: TF-IDF + regresión logística

El corpus original (`demo.csv`) y su modelo derivado (`model.json`) se conservan
solo en la instalación local y se excluyen de Git mientras no se autorice su
redistribución. Los comandos que los utilizan requieren disponer de esas copias
privadas. Esta carpeta conserva el código del experimento anterior.

El flujo incorpora un clasificador supervisado local, además del agente LLM
(Gemini, OpenAI o un modelo local compatible con las herramientas del agente).
El clasificador **ya está implementado**, pero su modelo inicial es de demostración:
se entrenó con **100 correos simulados** de `correos_simulados/correos.json`: 20 de accesos, 45 de aplicaciones, 25 de infraestructura y 10 de otros. No fue evaluado con
correos reales ni con un conjunto independiente. No se informa accuracy/F1.

## Funcionamiento en n8n

```text
Normalizar correo
  → Cargar modelo ML - PostgreSQL
  → Clasificar correo - TF-IDF
  → Seleccionar adjuntos para IA
  → Agente IA - Analizar solicitud
  → Comparar clasificaciones
  → Preparar ticket y validar en Redmine
```

El nodo **Clasificar correo - TF-IDF** convierte asunto y cuerpo en TF-IDF y aplica
los coeficientes de regresión logística entrenados con scikit-learn. El vocabulario,
IDF y coeficientes se leen desde **PostgreSQL**, no están incrustados en el código
del nodo. La inferencia se ejecuta en JavaScript dentro de n8n; no requiere Python
en el servidor, otra API, un cuarto contenedor ni llamadas de pago. El nodo de
consulta utiliza una credencial PostgreSQL de solo lectura.

## Almacenamiento en PostgreSQL

Se utiliza el servidor existente y la base `n8n`, en un esquema separado `ml`.
No se modifican las tablas internas de n8n ni de Redmine.

| Tabla | Contenido |
|---|---|
| `ml.modelos` | Versión, modelo completo en `artifact` (JSONB), indicador `activo` y fecha. |
| `ml.correos_entrenamiento` | Asunto, cuerpo, categoría y origen de los 100 ejemplos simulados, vinculados a la versión. |

Solo puede haber un modelo activo. Las predicciones siguen guardándose en las
ejecuciones de n8n y en la descripción del ticket, no en una nueva tabla ML.

La credencial **Mquito ML - PostgreSQL solo lectura** conecta a `postgres:5432`,
base `n8n`, usuario `mquito_ml_reader`. Su contraseña generada se conserva en
`.secrets/ml-postgres.json` y en las credenciales cifradas de n8n; no va en Git.
El usuario puede leer `ml.modelos`, pero no modificarlo ni leer los correos de
entrenamiento. La consulta fija es:

```sql
SELECT (SELECT artifact FROM ml.modelos WHERE activo = true LIMIT 1) AS modelo;
```

**Cargar modelo ML - PostgreSQL** ejecuta una consulta por correo, con timeout de
conexión de 5 segundos y `Continue (using regular output)` ante errores. El rol
limita cada consulta a 5 segundos. Si no hay modelo, devuelve una fila con `null`.
**Clasificar correo - TF-IDF** recupera el correo y sus adjuntos originales mediante
el enlace de items de n8n; ante modelo ausente, inválido o error SQL devuelve
`clasificacion_no_disponible` y continúa con el agente. La comparación admite esa
ausencia. No se borra ni se reemplaza el correo por la respuesta SQL.

Para preparar esta estructura en otra instalación, primero completar `.env` con
acceso administrativo a PostgreSQL y luego ejecutar desde una máquina con Python:

```bash
python -m pip install -r classifier/requirements.txt
python classifier/store-postgres.py
```

Este importador carga **solo la demostración**, comprueba que CSV y modelo coincidan,
preserva versiones y verifica el acceso de lectura. Después crear/seleccionar la
credencial PostgreSQL en n8n con los datos privados generados. No crea ni cambia
credenciales n8n automáticamente. No depende de reinicializar los volúmenes Docker.

Devuelve `clasificacion_ml` con categoría, probabilidades estimadas, tiempo de
inferencia, versión, origen de los datos y estado. Si no reconoce ninguna palabra
del vocabulario, devuelve categoría y probabilidad principal `null`, evitando
elegir una categoría solo por el intercepto. Conserva el correo y sus adjuntos.
Las probabilidades no se han calibrado ni constituyen garantía de acierto.

El agente sigue recibiendo solamente asunto, texto e inventario/archivos de su
entrada habitual: **no recibe la predicción ML**. El nodo **Comparar clasificaciones**
registra ambas categorías y si coinciden, y agrega una nota experimental a la
descripción del ticket. No cambia categoría, prioridad ni responsable propuestos
por el agente. La rama de error de IA mantiene el mecanismo de revisión existente;
en ese caso la predicción ML queda en la ejecución, sin comparación con el LLM.

Las salidas se consultan en **Executions → nodo → Output**. La comparación está
en `comparacion_tecnicas`; no se crea un segundo ticket ni una tabla de evaluación.
Si n8n elimina ejecuciones por su política de retención, estos registros también
pueden desaparecer; deben exportarse para un estudio formal.

## Configuración del modelo

| Parámetro | Valor |
|---|---|
| Categorías | accesos, aplicaciones, infraestructura, otros |
| Texto | Asunto (255 caracteres) + cuerpo (16000 caracteres) |
| Normalización | Minúsculas y eliminación de acentos |
| Tokens | Letras a-z y dígitos; mínimo 2 caracteres |
| Características | Unigramas y bigramas |
| TF-IDF | Frecuencia normal, IDF suavizado, normalización L2 |
| Clasificador | Regresión logística multiclase, solver lbfgs |
| C / max_iter | 1.0 / 1000 |
| Modelo activo | demo-v3, 100 ejemplos simulados |
| Decisión del ticket | Continúa a cargo del agente y validaciones existentes |

## Entrenar una nueva versión

Requiere Python y las dependencias en `requirements.txt` en la máquina de
entrenamiento. No instala nada dentro del contenedor n8n.

```bash
python -m pip install -r classifier/requirements.txt
python classifier/train.py
```

Para datos reales, preparar un CSV privado con columnas `asunto,cuerpo,categoria`.
Anonimizarlo, revisar las etiquetas y separar entrenamiento y prueba **antes** de
entrenar. Mantener conversaciones/duplicados en la misma partición para evitar
filtración. El script recibe exclusivamente el conjunto de entrenamiento:

```bash
python classifier/train.py --data tmp/correos-entrenamiento.csv --source real --version real-v1
node classifier/build-workflow.cjs workflows/correo-ia-redmine.json tmp/flujo-modelo-nuevo.json
node classifier/test.cjs tmp/flujo-modelo-nuevo.json
```

El script genera `model.json` con vocabulario, IDF, coeficientes y metadatos, y
`parity-fixtures.json` para contrastar la implementación Python con JavaScript.
El modelo exportado contiene vocabulario del entrenamiento: revisar que no incluya
datos personales antes de distribuirlo. Las credenciales no forman parte del modelo.

El generador actualiza los nodos de consulta, inferencia y comparación de forma idempotente en el archivo de salida.
**No publica cambios en el servidor**. Para actualizar el flujo existente, usar una
copia reciente de ese flujo para conservar sus cambios y credenciales; evitar
importar una segunda copia y activar ambas, porque podrían duplicar tickets.

Entrenar y generar un JSON **no actualiza el modelo activo de PostgreSQL**. Para
promover un modelo real, un administrador debe insertar una versión nueva en
`ml.modelos`, validar sus dimensiones/clases y activar esa versión dentro de una
transacción, desactivando la anterior. El nodo la leerá en la siguiente ejecución,
sin pegar coeficientes ni cambiar su código. `store-postgres.py` no publica modelos
reales; está limitado a la demostración para evitar etiquetar datos sintéticos
como reales. Una vez cargados los modelos, n8n no utiliza el archivo local `model.json`.

## Comparación académica pendiente

La comparación operativa muestra coincidencia entre técnicas, no precisión:
el agente actual también puede ver adjuntos y consultar herramientas. Para medir
clasificación de manera justa, usar un flujo de evaluación separado con el mismo
asunto/texto para ambos modelos, sin adjuntos ni predicción ML en la entrada del LLM.

Sobre correos de prueba etiquetados por una persona, medir accuracy, F1 macro,
matriz de confusión, tiempos y costo; no entrenar ni ajustar decisiones con ese
conjunto de prueba. Los ejemplos sintéticos sirven para comprobar la integración,
no para informar resultados sobre correos reales.

## Pruebas técnicas

```bash
node classifier/test.cjs
node workflows/test-workflow.cjs
node workflows/test-attachments.cjs
node workflows/test-assignment.cjs
```

Se verifica equivalencia numérica Python/JavaScript, textos vacíos y desconocidos,
preservación de adjuntos, aislamiento de la decisión del agente y rama de error.

Validación en el servidor (29/09/2026): la ejecución 10 completó la inferencia
local. La ejecución 11 obtuvo el análisis real del agente y detectó una
incompatibilidad de `structuredClone` en el nodo nuevo, que fue corregida.
La ejecución 12 reutilizó ese análisis y completó comparación, validación,
subida de adjuntos y creación del ticket de demostración **#9**, con responsable
validado. El clasificador propuso `aplicaciones` y el agente `accesos`; la discrepancia
quedó registrada en la descripción. Esto verifica integración, no precisión del
modelo. El flujo quedó guardado e inactivo, conservando su estado anterior.

Migración PostgreSQL (29/09/2026): ejecución 13 leyó el modelo desde la base y
conservó los tres adjuntos. Ejecución 14 verificó cuatro escenarios con dos correos
por escenario: modelo disponible, ausente, inválido y error SQL real. Todos
conservaron la correspondencia entre correo y adjunto y continuaron correctamente.
Estas pruebas no crearon tickets nuevos ni apagaron PostgreSQL.

Actualización demo-v2: 80 ejemplos simulados, 20 por categoría. Los 40 casos nuevos
incluyen contexto de trabajo, impacto, alcance y verificaciones previas. Son datos
de entrenamiento, no un conjunto de evaluación independiente. El modelo anterior
demo-v1 se conserva inactivo en PostgreSQL.


Actualización demo-v3: reemplaza al modelo activo con los 100 correos nuevos completos (asunto y cuerpo), incluidas faltas ortográficas y expresiones de malestar. Los archivos adjuntos no se usan como características del clasificador. Se usa `class_weight=balanced` para compensar el desequilibrio de categorías. demo-v2 queda inactivo como respaldo en PostgreSQL. No hay aprendizaje automático al recibir correos ni evaluación independiente de precisión.
