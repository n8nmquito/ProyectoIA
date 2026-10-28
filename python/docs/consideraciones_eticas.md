# Consideraciones éticas

## 1. Análisis de sesgos

### ¿El dataset tiene sesgos demográficos, culturales o de otro tipo?

Se utilizan conjuntos de **10, 100, 200 y 300 correos simulados en español**. Pueden tener sesgos de idioma, estilo de redacción y situaciones representadas. El conjunto de 300 incluye 90 correos de aplicaciones y 70 de cada categoría restante. No contiene atributos demográficos para analizar sesgos entre grupos de personas.

### ¿Cómo podrían afectar estos sesgos las predicciones?

El modelo puede asociar palabras o estilos repetidos con una categoría y equivocarse ante mensajes reales, abreviaturas, variantes del español u otros idiomas. Las métricas sobre datos simulados no garantizan el mismo rendimiento en producción.

### ¿Qué grupos podrían ser perjudicados?

Solicitantes que escriben en otros idiomas, usan términos poco frecuentes o presentan problemas escasamente representados. Una clasificación incorrecta puede derivar su solicitud al equipo equivocado y retrasar su atención.

## 2. Equidad y fairness

### ¿El modelo trata a todos los grupos de forma equitativa?

No se ha demostrado equidad entre grupos de personas. Aplicar el mismo modelo a todos los correos no garantiza resultados equitativos.

### Métricas de fairness evaluadas (si aplica)

No se calcularon métricas de fairness demográfica porque no se dispone de atributos ni muestras adecuados. Se utilizan **F1 macro, precisión, recall y F1 por categoría** para observar diferencias entre tipos de solicitud; estas métricas no demuestran equidad demográfica.

### Estrategias implementadas para mitigar inequidades

Se comparan resultados por categoría y se marcan para revisión predicciones con confianza inferior al **60 %** o sin vocabulario conocido. El prompt del agente indica no descartar solicitudes por faltas de ortografía o información incompleta. Se exploró la ponderación de clases, aunque la configuración final no la utiliza. Las señales de revisión no obligan por sí solas a una intervención humana.

## 3. Privacidad

### ¿Se utilizan datos personales o sensibles?

Los datasets del proyecto contienen correos simulados. En la operación, los correos, remitentes, adjuntos y consultas a Redmine pueden contener nombres, contactos, credenciales u otra información sensible.

### ¿Cómo se protege la privacidad de los usuarios?

El nodo de código **Limpiar firma y datos** de n8n elimina firmas habituales y redacta datos sensibles del asunto y cuerpo **antes de enviarlos a NexpAPI y al agente OpenAI**. La limpieza usa patrones, puede omitir datos y no anonimiza adjuntos ni respuestas de las herramientas. Los originales se conservan en n8n y Redmine.

NexpAPI exige `X-API-Key` y funciona dentro de la red Docker sin publicar el puerto 8000. Las claves se mantienen fuera de Git. El portal Streamlit procesa con Python sin llamar a OpenAI; su historial persistente guarda textos en SQLite y utiliza un enlace privado, que no equivale a autenticación. Las descargas también contienen textos y requieren cuidado al compartirlas.

### Cumplimiento con regulaciones (GDPR, CCPA, etc.)

No se ha realizado una auditoría ni se ha demostrado cumplimiento de GDPR, CCPA u otras regulaciones. El uso de datos simulados y la limpieza de texto no acreditan ese cumplimiento. Para operar con datos personales debe revisarse la normativa aplicable, el transporte seguro, los permisos, la retención y el tratamiento por proveedores externos.

## 4. Transparencia y explicabilidad

### ¿El modelo es interpretable?

El clasificador utiliza **TF-IDF y SVM lineal calibrada**. Sus coeficientes permiten inspeccionar términos asociados a cada categoría; no representan una comprensión humana del correo ni una explicación completa de cada predicción.

### ¿Los usuarios entienden cómo funciona?

La sección **Acerca de** del portal describe el modelo, sus parámetros, métricas disponibles y limitaciones. Los resultados muestran categoría, confianza, probabilidades y avisos de revisión. Python determina la categoría final; OpenAI prepara el análisis y propone prioridad, tipo y proyecto. Una confianza alta no garantiza un acierto.

### Técnicas de explicabilidad implementadas (SHAP, LIME, etc.)

Se inspeccionan coeficientes y términos asociados a las categorías mediante `top_terms`. **SHAP y LIME no están implementados**. Los gráficos de sensibilidad de hiperparámetros analizan el rendimiento, no explican individualmente cada correo.

## 5. Impacto social

### ¿Qué impacto positivo puede tener el proyecto?

Puede reducir tareas repetitivas de lectura, clasificación y registro, uniformar la derivación de solicitudes y facilitar su seguimiento en Redmine. El ahorro de tiempo y la satisfacción de los usuarios todavía no se han medido.

### ¿Qué impactos negativos podrían surgir?

Una categoría, prioridad o asignación incorrecta puede retrasar la atención. También pueden producirse resúmenes inexactos, exposición de información sensible o confianza excesiva en la automatización. El sistema no debe ser el único criterio para cerrar tickets, conceder accesos o resolver incidentes críticos.

### ¿Quiénes se benefician? ¿Quiénes podrían ser perjudicados?

Pueden beneficiarse operadores de mesa de ayuda, técnicos de soporte TI, supervisores y solicitantes. Pueden resultar perjudicados quienes reciban una derivación incorrecta, presenten casos poco representados o tengan datos personales en correos y adjuntos procesados.

## 6. Responsabilidad

### ¿Quién es responsable si el modelo falla?

El equipo de soporte debe revisar y corregir la atención de los tickets; el equipo técnico mantiene el modelo y la integración. **María Quito Castillo**, líder del proyecto y desarrolladora full stack, coordina la revisión y las correcciones. Los demás responsables nominales están pendientes de completar.

### ¿Qué mecanismos de accountability existen?

Git registra cambios del código y se conservan configuraciones, hashes de modelos, reportes de evaluación y ejecuciones de n8n para investigar errores. El flujo valida categorías, proyectos, responsables, membresías y roles contra Redmine. Si Python no devuelve una clasificación válida, deriva a revisión sin crear el ticket. No existe aprobación humana obligatoria antes de cada alta ni monitoreo automático de deriva del modelo.

### Plan de monitoreo y actualización del modelo

**Plan propuesto; todavía no es una rutina periódica implementada:**

1. Revisar semanalmente una muestra de tickets, errores y avisos de baja confianza; registrar la versión y la corrección humana.
2. Separar fallos del modelo de problemas de integración o asignación y derivarlos a soporte o desarrollo.
3. Preparar datos nuevos autorizados y etiquetados por personas, con un conjunto de evaluación separado del entrenamiento.
4. Comparar F1 macro, accuracy, métricas por categoría y baseline antes de aprobar una actualización.
5. Coordinar la aprobación con la líder del proyecto y soporte; conservar el modelo y la configuración anteriores para poder revertir.
