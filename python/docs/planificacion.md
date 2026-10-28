# Planificación del sistema de clasificación de tickets TI

El proyecto prueba versiones de 10, 100, 200 y 300 correos y adopta
**modelo_clasificador_300.pkl como modelo final**. Las tres versiones menores
se conservan para comparación; las métricas por versión se detallan en la evaluación actual.

Versión: 27 de octubre de 2026.

## Definición del problema y objetivos

Los correos de soporte mezclan consultas sobre cuentas, errores de aplicaciones,
equipos, redes y dudas generales. El operador debe leerlos y decidir quién los
atiende. El proyecto propone una categoría inicial para apoyar esa tarea y
facilitar su supervisión. En la automatización actual, Python determina la
categoría final; el agente prepara el análisis y el código crea el ticket
después de resolver el responsable por categoría y validar los datos de Redmine.

### Objetivo general

Desarrollar un sistema de clasificación de solicitudes de soporte TI que permita
entrenar, guardar y probar un clasificador de texto reproducible e integrarlo al
flujo de correo, n8n y Redmine para apoyar la derivación inicial de tickets.

### Objetivos específicos

- Preparar y validar los correos, combinar título y cuerpo y analizar la calidad
  y distribución de las cuatro categorías.
- Comparar una referencia mayoritaria, regresión logística y SVM calibrada
  mediante métricas de clasificación y validación cruzada.
- Optimizar los hiperparámetros y conservar modelos y datasets correspondientes
  a 10, 100, 200 y 300 correos, con trazabilidad entre ambos.
- Permitir pruebas por consola y Streamlit, mostrando categoría, probabilidades
  y advertencias cuando la predicción requiere revisión.
- Exponer el modelo de 300 mediante una API interna e integrarlo con la
  automatización para comparar su predicción con la propuesta del agente.
- Documentar resultados, limitaciones, pruebas, recursos y riesgos del sistema.

## Justificación de la relevancia del proyecto

La relevancia está en reducir trabajo repetitivo y hacer visible cuándo hace
falta revisión manual. No se midieron ahorros de tiempo ni beneficios económicos;
son objetivos de uso futuro, no resultados comprobados.

Comparar modelos con distintas cantidades de correos permite estudiar el
comportamiento del clasificador con un corpus reducido. La integración con
Redmine permite comprobar el circuito de registro y asignación de solicitudes,
mientras que la consola y Streamlit facilitan la demostración y revisión de
predicciones. Su utilidad en una mesa de ayuda real requiere validación con
datos autorizados y supervisión del personal de soporte.

## Alcance del proyecto

### Qué incluye

Incluye cuatro categorías; un JSON maestro de 300 correos simulados; datasets
de 10/100/200/300; cuatro modelos guardados; pruebas por consola con selección
de modelo; entrenamiento y evaluación; gráficos, notebooks y documentación.
Las categorías son accesos, aplicaciones, infraestructura y otros.
También incluye Streamlit, una API Python en Docker y la integración con n8n,
OpenAI y Redmine para registrar solicitudes y comprobar asignaciones.

El flujo desplegado lee el buzón, envía texto y adjuntos seleccionados al agente,
crea tickets y puede enviar avisos. Streamlit continúa local; la API está
desplegada en una red Docker interna. Python clasifica la categoría; el agente
propone también prioridad y responsable, sujetos a las validaciones del flujo.

### Qué no incluye

- Resolución automática de incidentes o modificación real de permisos y cuentas.
- Entrenamiento de un predictor Python independiente de prioridad o grupo.
- Implementación de embeddings semánticos: la representación actual usa TF-IDF.
- Despliegue público de Streamlit o exposición pública de la API Python.
- Demostración de ahorro de tiempo, beneficios económicos o generalización a
  correos reales; no hay una evaluación con usuarios finales externos.

La publicación del repositorio y los videos forman parte de la entrega
académica, pero siguen pendientes según la documentación actual.

### Criterios de aceptación y estado real

| Criterio | Evidencia actual |
|---|---|
| Cargar y validar correos | src/data_processing.py y pruebas asociadas |
| Combinar título y cuerpo | combine_text aplicado antes de entrenar o predecir |
| Comparar baseline, LR y SVM | results/metrics/model_comparison.csv |
| Buscar hiperparámetros | grid_search.csv y sensitivity.json |
| Guardar cuatro tamaños exactos | models/ y data/train/; cantidades verificadas |
| Elegir modelo desde CMD | evaluar_nuevos.py --model 10/100/200/300 |
| Mostrar dudas y texto del ticket | requiere_revision y detalle en consola |
| Probar funciones críticas | 90 pruebas automatizadas aprobadas |
| Explicar resultados y límites | seis documentos requeridos y evaluación complementaria |

## Cronograma de desarrollo planificado vs real

Fuente: **Cronograma.docx**, proporcionado por el equipo. Las fechas siguientes
reproducen sus tablas de planificación y ejecución real. Todos los períodos
corresponden a 2026; los adelantos se calculan en días calendario respecto de
la fecha de fin planificada.

| Fase | Período planificado | Período real informado | Variación del cierre | Responsable |
|---|---|---|---|---|
| Exploración de Datos | 14/09/2026 al 20/09/2026 | 14/09/2026 al 20/09/2026 | Sin variación | Data Scientist + Experto Soporte TI |
| Prototipo/MVP | 21/09/2026 al 27/09/2026 | 21/09/2026 al 27/09/2026 | Sin variación | Data Scientist |
| Desarrollo | 28/09/2026 al 15/10/2026 | 28/09/2026 al 11/10/2026 | 4 días antes | Data Scientist / Desarrollador TI |
| Testing | 16/10/2026 al 20/10/2026 | 12/10/2026 al 18/10/2026 | 2 días antes | Equipo IA + Soporte TI |
| Deploy Piloto | 21/10/2026 al 23/10/2026 | 19/10/2026 al 22/10/2026 | 1 día antes | TI + Mesa de Ayuda |
| Deploy Completo | 26/10/2026 al 30/10/2026 | 23/10/2026 al 25/10/2026 | 5 días antes | TI + Líder del Proyecto |

### Entregables y diferencias de ejecución

| Fase | Entregable planificado | Entregable real registrado en el cronograma |
|---|---|---|
| Exploración de Datos | Acceso a datos, anonimización, EDA y Data Quality Report | Acceso a datos, sintetización de datos preclasificados, EDA y Data Quality Report |
| Prototipo/MVP | Dataset preparado, baseline TF-IDF y regresión logística | Sin cambio de entregable |
| Desarrollo | Embeddings, clasificador, comparación de modelos y API simulada | Sin cambio de descripción en el cronograma |
| Testing | Validación de categoría, prioridad/grupo por separado y Testing Plan | Sin cambio de entregable |
| Deploy Piloto | Prueba controlada del agente | Sin cambio de entregable |
| Deploy Completo | MVP final, documentación y monitoreo inicial | Sin cambio de entregable |

El cronograma informa un cierre global el **25 de octubre de 2026**, cinco días
antes del 30 de octubre previsto. La exploración y el prototipo mantienen sus
fechas; el adelanto del cierre de Desarrollo permite anticipar las fases
siguientes. No se registran causas adicionales que expliquen los cambios.

La descripción de entregables del cronograma debe leerse junto con la evidencia
técnica actual: se implementó TF-IDF con SVM calibrada y una API Python interna
en Docker. La mención de embeddings y API simulada se conserva como descripción
del cronograma, sin atribuirles una implementación que no existe. La prioridad
y el grupo se gestionan en el flujo del agente y Redmine; las métricas del
clasificador Python corresponden a categoría.

El cierre informado de Deploy Completo no equivale a una entrega académica
íntegra: al 27 de octubre siguen pendientes los datos de integrantes, la
publicación del código y los enlaces de los videos. La documentación y las
verificaciones actuales incluyen revisiones posteriores al cierre informado.
El monitoreo inicial figura como entregable del cronograma; su inclusión no
demuestra por sí sola una operación prolongada ni una evaluación externa.

## Recursos necesarios

### Datos

- JSON maestro con 300 correos simulados y cuatro categorías: 70 de accesos,
  90 de aplicaciones, 70 de infraestructura y 70 de otros.
- Datasets anidados de 10, 100, 200 y 300 correos y los cuatro modelos asociados.
- Conjunto de 25 correos sin etiquetas, separado del entrenamiento, para
  comparar predicciones y revisar regresiones; no permite calcular aciertos.
- Etiquetado humano y autorización de uso para una futura evaluación con
  correos reales. El corpus y los datasets se incluyen en Git por indicación
  de la responsable del proyecto; su licencia de uso se distingue de la del código.

### Hardware

Una computadora con CPU y almacenamiento para el corpus, los modelos, las
dependencias y los resultados permite entrenar y ejecutar consola y Streamlit.
No se usa GPU. La operación integrada necesita un servidor capaz de ejecutar
los contenedores Docker y conectividad con el buzón y los servicios externos.
No se han establecido mínimos medidos de RAM, CPU o espacio en disco.

### Software y servicios

Python 3.10/3.11 y las dependencias de `requirements.txt`: pandas, scikit-learn,
joblib, Streamlit, pytest, matplotlib y seaborn, entre otras. Para la operación
integrada se necesitan Docker y Compose, n8n, Redmine, PostgreSQL, acceso al
buzón y una credencial OpenAI. El servidor y el consumo de servicios pueden
generar costes; no se ha fijado un presupuesto en la documentación.

### Recursos humanos

Se requiere que una persona del área revise la definición de categorías y que
los integrantes del equipo validen los resultados y expliquen las decisiones.
No se registró una evaluación con usuarios finales externos.

María Quito Castillo asume los roles Líder del Proyecto y Desarrollador TI
(desarrolladora full stack). Los nombres de los responsables de Data Scientist,
Experto Soporte TI, Equipo IA, Soporte TI, TI y Mesa de Ayuda quedan por completar
en la sección de autores del README.

## Riesgos identificados y mitigación

| Riesgo | Medida aplicada o pendiente |
|---|---|
| Confundir permisos con fallos de aplicación | Ejemplos contrastados y revisión manual; el riesgo continúa |
| Pocos datos o estilo sintético repetido | Procedencia declarada; se requiere validación real futura |
| Mezclar entrenamiento y prueba | Los 25 permanecen fuera de fit; se comprueban coincidencias exactas |
| Presentar confianza como certeza | Avisos en consola, interfaz y documentación |
| Exponer información sensible | Ejemplos ficticios y limpieza parcial; revisar antes de usar datos reales |
| Perder correspondencia modelo/dataset | Índices, etiquetas, huellas y hashes verificables |
| Cambiar archivos al volver a entrenar | Nombres estables y trazabilidad; conservar versiones antes de cambios importantes |
| Entrega académica incompleta | Lista explícita de autores, repositorio, soporte y videos pendientes |
| Fallos de API, buzón o servicios externos | Autenticación y validación de entradas, manejo de fallos del flujo y pruebas de recuperación; revisar la operación y los costes |
| Asignación incorrecta de prioridad o responsable | Validación de catálogos, membresía y rol antes del alta; supervisión del personal de soporte |

### Próximo trabajo recomendado

Recoger un conjunto realmente nuevo y autorizado, etiquetado por una persona
que no use las predicciones como respuesta esperada. Mantenerlo separado mientras
se evalúan cambios. Antes de usar el sistema en una organización, acordar
responsables, retención de datos y un proceso de revisión de errores.

### Interfaz de usuario para la revisión

La interfaz usa Streamlit, opción A de la rúbrica. Permite seleccionar modelos
de 10, 100, 200 o 300 correos, ingresar título y descripción, cargar ejemplos
y mostrar categoría, confianza y cuatro probabilidades. Incluye validación,
indicador de procesamiento, manejo de errores e información del modelo.
La navegación utiliza un selector centrado con Clasificar y Acerca de.
La automatización de correo en n8n funciona como componente separado.
