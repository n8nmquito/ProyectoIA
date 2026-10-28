# Planificación del proyecto

## 1. Definición del problema y objetivos

### Definición del problema

La mesa de ayuda recibe correos sobre cuentas, aplicaciones, equipos, redes y consultas generales. Leerlos, clasificarlos, preparar el ticket y derivarlo manualmente son tareas repetitivas que pueden producir asignaciones inconsistentes y demoras. El proyecto automatiza ese recorrido con un clasificador Python, un agente OpenAI y validaciones antes del registro en Redmine.

### Objetivo general

Desarrollar e integrar un sistema reproducible de clasificación de correos de soporte TI que determine su categoría y automatice la preparación, validación y registro de tickets en Redmine mediante n8n, con una interfaz para probar y revisar los modelos.

### Objetivos específicos

- Preparar los datasets simulados de **10, 100, 200 y 300 correos**, validar su calidad y analizar las cuatro categorías.
- Comparar baseline, regresión logística y SVM calibrada; seleccionar hiperparámetros mediante F1 macro y documentar el análisis del Workshop S5.
- Entrenar y conservar las cuatro versiones con trazabilidad entre datos, configuración, modelos y resultados.
- Ofrecer pruebas por consola y Streamlit con categoría, confianza, probabilidades, ejemplos, historial, comparación y exportación.
- Integrar el modelo de 300 mediante **NexpAPI**; limpiar firmas y datos sensibles en n8n antes de consultar el clasificador y OpenAI.
- Aplicar la categoría final de Python, validar los datos de Redmine y registrar el ticket con el responsable configurado cuando sea válido.
- Documentar la planificación, los datos, la arquitectura, la optimización y las consideraciones éticas.

## 2. Justificación de la relevancia del proyecto

Una solicitud mal clasificada o derivada puede tardar más en llegar al equipo adecuado. Automatizar las tareas repetitivas y aplicar criterios uniformes permite organizar la atención y conservar la trazabilidad de categoría, análisis y asignación en Redmine.

El portal facilita que operadores, técnicos y supervisores prueben las predicciones y revisen sus limitaciones. Comparar tamaños de dataset permite explorar el comportamiento del clasificador con pocos ejemplos. **La reducción de tiempos y la mejora de la atención son objetivos; todavía no se han medido con usuarios finales externos.** La utilidad en una organización requiere validación con datos autorizados y supervisión de soporte.

## 3. Alcance (qué incluye y qué NO incluye)

### Qué incluye

- Clasificación de solicitudes en **accesos, aplicaciones, infraestructura y otros**.
- Corpus simulado de 300 correos, muestras anidadas de 10/100/200/300 y 25 correos separados para pruebas funcionales y revisión manual.
- Preprocesamiento, EDA, comparación de modelos, optimización, entrenamiento, evaluación y trazabilidad de artefactos.
- Portal Streamlit local o desplegado en Docker, con selección de modelos disponibles, ejemplos, resultados, temas, idiomas, descargas, historial y comparación.
- NexpAPI interna con el modelo de 300 y autenticación; n8n para recibir correo, limpiar texto, consultar el clasificador y ejecutar el agente OpenAI.
- Preparación y validación de tickets, resolución de responsables, carga de adjuntos y registro en Redmine, con avisos según el flujo configurado.
- Código versionado en **main** y los cinco documentos requeridos en `python/docs/`.

### Qué NO incluye

- Resolver automáticamente incidentes, modificar cuentas o conceder/revocar permisos.
- Cerrar tickets o tomar decisiones críticas basándose únicamente en el modelo.
- Entrenar un modelo Python independiente de prioridad o grupo; esos datos se gestionan mediante el agente y las validaciones del flujo.
- Embeddings semánticos, entrenamiento de redes neuronales o ajuste de un LLM; la representación implementada es TF-IDF.
- Exponer NexpAPI directamente en Internet; se comunica por la red interna Docker.
- Garantizar anonimización completa, fairness demográfica, exactitud o generalización a correos reales.
- Monitoreo automático de deriva, aprendizaje en línea o aprobación humana obligatoria antes de cada ticket.

Los nombres del resto del equipo, la licencia pendiente del README y los enlaces de videos permanecen por completar en sus espacios de entrega. La publicación de cambios en Git ya está realizada.

## 4. Cronograma de desarrollo (planificado vs real)

**Fuente: Cronograma.docx, proporcionado por el equipo.** Las fechas y roles siguientes corresponden a sus tablas de planificación y ejecución real. Todos los períodos son de **2026**; la variación compara las fechas de cierre en días calendario.

| Fase | Período planificado | Período real informado | Variación del cierre | Responsable del cronograma |
|---|---|---|---|---|
| Exploración de Datos | 14/09/2026 al 20/09/2026 | 14/09/2026 al 20/09/2026 | Sin variación | Data Scientist + Experto Soporte TI |
| Prototipo/MVP | 21/09/2026 al 27/09/2026 | 21/09/2026 al 27/09/2026 | Sin variación | Data Scientist |
| Desarrollo | 28/09/2026 al 15/10/2026 | 28/09/2026 al 11/10/2026 | 4 días antes | Data Scientist / Desarrollador TI |
| Testing | 16/10/2026 al 20/10/2026 | 12/10/2026 al 18/10/2026 | 2 días antes | Equipo IA + Soporte TI |
| Deploy Piloto | 21/10/2026 al 23/10/2026 | 19/10/2026 al 22/10/2026 | 1 día antes | TI + Mesa de Ayuda |
| Deploy Completo | 26/10/2026 al 30/10/2026 | 23/10/2026 al 25/10/2026 | 5 días antes | TI + Líder del Proyecto |

### Entregables y correspondencia con la implementación

| Fase | Entregable del cronograma | Implementación y estado documentados |
|---|---|---|
| Exploración de Datos | Plan: acceso, anonimización, EDA y Data Quality Report. Real: acceso, sintetización de datos preclasificados, EDA y Data Quality Report | Datasets simulados, validaciones, estadísticas y seis gráficos EDA |
| Prototipo/MVP | Dataset preparado, baseline TF-IDF y regresión logística | Comparación de referencia mayoritaria, regresión logística y SVM |
| Desarrollo | Embeddings, clasificador, comparación de modelos y API simulada | Se implementaron TF-IDF, SVM calibrada y NexpAPI real en Docker; no embeddings |
| Testing | Categoría, prioridad/grupo por separado y Testing Plan | Métricas de categoría, pruebas Python y validaciones de integración/asignación; no modelo Python separado de prioridad/grupo |
| Deploy Piloto | Prueba controlada del agente | Ejecuciones diagnósticas con datos ficticios y controles que evitan crear tickets o enviar correos durante esas pruebas |
| Deploy Completo | MVP final, documentación y monitoreo inicial | Portal, NexpAPI y flujo desplegados; código en main y cinco documentos. El monitoreo automático de deriva no está implementado |

El documento informa cierre de Deploy Completo el **25/10/2026**, cinco días antes del **30/10/2026** previsto. No registra causas adicionales para los adelantos. La tabla reproduce lo informado; no convierte en implementados los entregables que la evidencia técnica no demuestra.

Las revisiones de documentación e integración continuaron hasta el **28/10/2026**, después del cierre informado. La última verificación de código registró **91 pruebas Python aprobadas**, además de suites JavaScript y pruebas aisladas de n8n. Los videos y datos pendientes del equipo no se consideran completados por el cierre del cronograma.

María Quito Castillo asume los roles **Líder del Proyecto y Desarrollador TI** (desarrolladora full stack). Los demás nombres de responsables quedan pendientes de completar; se conservan los roles originales del cronograma.

## 5. Recursos necesarios (datos, hardware, software)

### Datos

- [Corpus maestro de 300 correos simulados](../data/raw/correos.json): 70 de accesos, 90 de aplicaciones, 70 de infraestructura y 70 de otros.
- [Muestras de entrenamiento de 10, 100, 200 y 300](../data/train/), modelos correspondientes y configuración reproducible.
- [25 correos de prueba](../data/test/correos_test_25.json) para ejecutar predicciones y revisarlas manualmente, sin exigir etiquetas para esa finalidad.
- Para una evaluación futura con datos reales: autorización de uso y etiquetas esperadas revisadas por personas, separadas del entrenamiento.

### Hardware

Se necesita una computadora con CPU y almacenamiento para los datos, modelos, dependencias y resultados; **no se requiere GPU**. La integración necesita un VPS con Docker y conectividad con el buzón, OpenAI y los servicios del proyecto.

El Compose de NexpAPI asigna un límite de **1 CPU y 512 MiB de memoria a ese contenedor**. Es una configuración de despliegue, no un mínimo medido para todo el sistema. No se han determinado requisitos mínimos globales de RAM, CPU o disco. Los volúmenes persistentes almacenan PostgreSQL, adjuntos de Redmine e historial SQLite.

### Software

- **Python 3.10.22** en los contenedores, con las dependencias fijadas de clasificación, análisis e interfaz.
- **scikit-learn, pandas, NumPy, SciPy, joblib y PyYAML** para datos, modelos y configuración; **Streamlit y Altair** para la interfaz y visualizaciones.
- **FastAPI y Uvicorn** para NexpAPI; **Docker y Compose** para despliegue y reinicio de servicios.
- **n8n, Redmine y PostgreSQL**, más acceso IMAP/SMTP al buzón y credencial del agente **OpenAI gpt-4.1-mini**.
- **Git** para versionamiento; **pytest y Ruff** para pruebas y revisión del código.

Las versiones están detalladas en [arquitectura](arquitectura.md). Se necesitan cuentas y permisos válidos para los servicios. El VPS y el consumo de OpenAI generan costes; no hay un presupuesto cuantificado registrado.

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
| Entrega académica incompleta | Código en main, cinco documentos ordenados y espacios identificados en el README | Completar integrantes, licencia pendiente y enlaces de los dos videos |

El equipo debe acordar responsables de seguimiento y una revisión periódica de errores antes de operar con solicitudes reales. El plan de monitoreo y actualización está descrito como propuesta en [consideraciones éticas](consideraciones_eticas.md); no se presenta como una rutina automática implementada.
