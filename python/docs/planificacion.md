# Planificación del proyecto

## 1. Definición del problema y objetivos

### Definición del problema

La mesa de ayuda debe leer correos, clasificarlos y decidir a quién asignarlos. Son tareas repetitivas que pueden causar demoras o derivaciones inconsistentes. El proyecto automatiza ese recorrido con Python, n8n, OpenAI y Redmine.

### Objetivo general

Crear un sistema reproducible que clasifique correos de soporte TI y registre tickets validados en Redmine mediante n8n, con una interfaz para probar y revisar los modelos.

### Objetivos específicos

- Preparar los datasets simulados de **10, 100, 200 y 300 correos**, validar su calidad y analizar las cuatro categorías.
- Comparar baseline, regresión logística y SVM calibrada; seleccionar hiperparámetros mediante F1 macro y documentar el análisis del Workshop S5.
- Entrenar y conservar las cuatro versiones con trazabilidad entre datos, configuración, modelos y resultados.
- Ofrecer pruebas por consola y Streamlit con categoría, confianza, probabilidades, ejemplos, historial, comparación y exportación.
- Integrar el modelo de 300 mediante **NexpAPI**; limpiar firmas y datos sensibles en n8n antes de consultar el clasificador y OpenAI.
- Aplicar la categoría final de Python, validar los datos de Redmine y registrar el ticket con el responsable configurado cuando sea válido.
- Documentar la planificación, los datos, la arquitectura, la optimización y las consideraciones éticas.

## 2. Justificación de la relevancia del proyecto

Una mala derivación retrasa la atención. El sistema busca reducir tareas repetitivas, aplicar criterios uniformes y dejar trazabilidad de categoría, análisis y asignación en Redmine.

El portal permite probar las respuestas y comparar modelos con pocos datos. **Todavía no se han medido ahorro de tiempo ni mejoras con usuarios externos.** El uso real requiere datos autorizados y supervisión de soporte.

## 3. Alcance (qué incluye y qué NO incluye)

### Qué incluye

- Clasificación de solicitudes en **accesos, aplicaciones, infraestructura y otros**.
- Corpus simulado de 300 correos, muestras anidadas de 10/100/200/300 y 25 correos separados para pruebas funcionales y revisión manual.
- Preprocesamiento, EDA, comparación de modelos, optimización, entrenamiento, evaluación y trazabilidad de artefactos.
- Portal Streamlit local o desplegado en Docker, con selección de modelos disponibles, ejemplos, resultados, temas, idiomas, descargas, historial y comparación.
- NexpAPI interna con el modelo de 300 y autenticación; n8n para recibir correo, limpiar texto, consultar el clasificador y ejecutar el agente OpenAI.
- Preparación y validación de tickets, resolución de responsables, carga de adjuntos y registro en Redmine, con avisos según el flujo configurado.
- Código versionado en **main** y los seis documentos requeridos en `python/docs/`.

### Qué NO incluye

- Resolver automáticamente incidentes, modificar cuentas o conceder/revocar permisos.
- Cerrar tickets o tomar decisiones críticas basándose únicamente en el modelo.
- Entrenar un modelo Python independiente de prioridad o grupo; esos datos se gestionan mediante el agente y las validaciones del flujo.
- Embeddings semánticos, entrenamiento de redes neuronales o ajuste de un LLM; la representación implementada es TF-IDF.
- Exponer NexpAPI directamente en Internet; se comunica por la red interna Docker.
- Garantizar anonimización completa, fairness demográfica, exactitud o generalización a correos reales.
- Monitoreo automático de deriva, aprendizaje en línea o aprobación humana obligatoria antes de cada ticket.

Faltan los nombres del resto del equipo, el apartado de licencia del README y los enlaces de videos. El código ya está subido a Git.

## 4. Cronograma de desarrollo (planificado vs real)

**Fuente: Cronograma.docx, entregado por el equipo.** Se conservan sus fechas y roles. Los períodos son de **2026** y la variación se calcula en días calendario sobre la fecha de cierre.

| Fase | Período planificado | Período real informado | Variación del cierre | Responsable del cronograma |
|---|---|---|---|---|
| Exploración de Datos | 14/09/2026 al 20/09/2026 | 14/09/2026 al 20/09/2026 | Sin variación | Data Scientist + Experto Soporte TI |
| Prototipo/MVP | 21/09/2026 al 27/09/2026 | 21/09/2026 al 27/09/2026 | Sin variación | Data Scientist |
| Desarrollo | 28/09/2026 al 11/10/2026 | 28/09/2026 al 15/10/2026 | 4 días después | Data Scientist / Desarrollador TI |
| Testing | 12/10/2026 al 18/10/2026 | 16/10/2026 al 20/10/2026 | 2 días después | Equipo IA + Soporte TI |
| Deploy Piloto | 19/10/2026 al 22/10/2026 | 21/10/2026 al 23/10/2026 | 1 día después | TI + Mesa de Ayuda |
| Deploy Completo | 23/10/2026 al 25/10/2026 | 26/10/2026 al 30/10/2026 | 5 días después | TI + Líder del Proyecto |

### Entregables y correspondencia con la implementación

| Fase | Entregable del cronograma | Implementación y estado documentados |
|---|---|---|
| Exploración de Datos | Plan: acceso, anonimización, EDA y Data Quality Report. Real: acceso, sintetización de datos preclasificados, EDA y Data Quality Report | Datasets simulados, validaciones, estadísticas y seis gráficos EDA |
| Prototipo/MVP | Dataset preparado, baseline TF-IDF y regresión logística | Comparación de referencia mayoritaria, regresión logística y SVM |
| Desarrollo | Embeddings, clasificador, comparación de modelos y API simulada | Se implementaron TF-IDF, SVM calibrada y NexpAPI real en Docker; no embeddings |
| Testing | Categoría, prioridad/grupo por separado y Testing Plan | Métricas de categoría, pruebas Python y validaciones de integración/asignación; no modelo Python separado de prioridad/grupo |
| Deploy Piloto | Prueba controlada del agente | Ejecuciones diagnósticas con datos ficticios y controles que evitan crear tickets o enviar correos durante esas pruebas |
| Deploy Completo | MVP final, documentación y monitoreo inicial | Portal, NexpAPI y flujo desplegados; código en main y seis documentos. El monitoreo automático de deriva no está implementado |

El cronograma informa cierre real el **30/10/2026**, cinco días después del **25/10/2026** propuesto, sin explicar los retrasos. Esa fecha no demuestra que se hayan implementado todos los entregables mencionados.

Hubo revisiones hasta el **28/10/2026**, dentro del período de Deploy Completo informado. La última comprobación registró **96 pruebas Python aprobadas**, más pruebas JavaScript y de n8n. Los videos y datos pendientes del equipo siguen por completar.

**María Quito Castillo** es Líder del Proyecto y Desarrollador TI (desarrolladora full stack). Los otros nombres quedan pendientes; se mantienen los roles del cronograma.

## 5. Recursos necesarios (datos, hardware, software)

### Datos

- [Corpus maestro de 300 correos simulados](../data/raw/correos.json): 70 de accesos, 90 de aplicaciones, 70 de infraestructura y 70 de otros.
- [Muestras de entrenamiento de 10, 100, 200 y 300](../data/train/), modelos correspondientes y configuración reproducible.
- [25 correos de prueba](../data/test/correos_test_25.json) para ejecutar predicciones y revisarlas manualmente, sin exigir etiquetas para esa finalidad.
- Para una evaluación futura con datos reales: autorización de uso y etiquetas esperadas revisadas por personas, separadas del entrenamiento.

### Hardware

Se necesita CPU y espacio para datos, modelos y dependencias; **no se usa GPU**. El flujo integrado requiere un VPS con Docker y conexión al buzón y a OpenAI.

NexpAPI tiene un límite de **1 CPU y 512 MiB**. No es un mínimo medido para todo el sistema: faltan requisitos globales de RAM, CPU y disco. Los volúmenes guardan PostgreSQL, adjuntos e historial SQLite.

### Software

- **Python 3.10.22** en los contenedores, con las dependencias fijadas de clasificación, análisis e interfaz.
- **scikit-learn, pandas, NumPy, SciPy, joblib y PyYAML** para datos, modelos y configuración; **Streamlit y Altair** para la interfaz y visualizaciones.
- **FastAPI y Uvicorn** para NexpAPI; **Docker y Compose** para despliegue y reinicio de servicios.
- **n8n, Redmine y PostgreSQL**, más acceso IMAP/SMTP al buzón y credencial del agente **OpenAI gpt-4.1-mini**.
- **Git** para versionamiento; **pytest y Ruff** para pruebas y revisión del código.

Las versiones están en [arquitectura](arquitectura.md). Se requieren cuentas y permisos para los servicios. El VPS y OpenAI tienen costes; no hay un presupuesto registrado.

## 6. Riesgos identificados y mitigación

| Riesgo | Mitigación implementada | Acción pendiente o límite |
|---|---|---|
| Clasificación incorrecta o datos poco representativos | Comparación con baseline, métricas por clase, probabilidades y avisos de baja confianza | Validar con datos reales autorizados y revisión humana |
| Sobreajuste al estilo de correos simulados | Procedencia declarada, validación cruzada y separación de casos funcionales | Incorporar una prueba externa nueva; no presentar los 25 conocidos como evaluación independiente |
| Confundir confianza con certeza | Advertencias en el portal y señal de revisión bajo 60 % o sin vocabulario conocido | La señal no obliga a una revisión humana; acordar un procedimiento operativo |
| Exposición de datos sensibles | Nodo local n8n que limpia firmas y redacta datos antes de NexpAPI/OpenAI; API interna y claves fuera de Git | No anonimiza adjuntos ni todos los datos; revisar accesos, transporte y retención antes de usar información real |
| Fallos del buzón, NexpAPI o servicios externos | Comprobaciones de salud, manejo de errores y derivación a revisión; reinicio de contenedores unless-stopped | Investigar y reintentar sin duplicar tickets; acordar seguimiento operativo |
| Categoría, tipo, proyecto o responsable incorrectos | Categoría Python obligatoria y validación contra catálogos, membresías y roles reales de Redmine | Supervisar asignaciones y corregir tickets cuando corresponda |
| Duplicar tickets al reprocesar correos | Cursor IMAP que evita reprocesar mensajes antiguos ya considerados | No existe garantía global de idempotencia; comprobar Redmine antes de reintentar una ejecución |
| Perder correspondencia entre datos y modelos | Datasets por tamaño, hashes, configuración y reportes registrados | Conservar artefactos anteriores antes de reentrenar y reevaluar cada nueva versión |
| Costes o dependencia del proveedor externo | El clasificador Python funciona sin OpenAI; la API y el portal ejecutan el modelo localmente | Definir presupuesto y revisar consumo; el análisis del agente depende del servicio externo |
| Entrega académica incompleta | Código en main, seis documentos ordenados y espacios identificados en el README | Completar integrantes, licencia pendiente y enlaces de los dos videos |

Antes de operar con correos reales, hay que asignar responsables y acordar cómo revisar errores. El [plan de monitoreo](consideraciones_eticas.md) sigue siendo una propuesta, no una rutina automática.
