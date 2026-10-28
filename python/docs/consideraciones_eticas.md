# Consideraciones éticas

## 1. Análisis de sesgos

### ¿El dataset tiene sesgos demográficos, culturales o de otro tipo?

Usamos **10, 100, 200 y 300 correos simulados en español**. Pueden repetir estilos y situaciones. En el conjunto de 300 hay 90 correos de aplicaciones y 70 de cada categoría restante. No hay atributos demográficos para evaluar sesgos entre personas.

### ¿Cómo podrían afectar estos sesgos las predicciones?

El modelo puede aprender palabras o estilos repetidos y fallar con mensajes reales, abreviaturas u otros idiomas. Los resultados sobre correos simulados no garantizan el mismo desempeño en producción.

### ¿Qué grupos podrían ser perjudicados?

Usuarios que escriben en otros idiomas o plantean problemas poco representados. Una mala clasificación puede retrasar su atención o enviarlos al equipo equivocado.

## 2. Equidad y fairness

### ¿El modelo trata a todos los grupos de forma equitativa?

No se ha demostrado. Usar el mismo modelo para todos no garantiza resultados equitativos.

### Métricas de fairness evaluadas (si aplica)

No se midió fairness demográfica porque faltan atributos y muestras adecuados. **F1 macro y las métricas por categoría** permiten comparar tipos de solicitud, pero no prueban equidad entre personas.

### Estrategias implementadas para mitigar inequidades

Se revisan métricas por categoría y se marcan predicciones con confianza inferior al **60 %** o sin vocabulario conocido. El agente no debe descartar soporte por faltas de ortografía o información incompleta. Se probó ponderar clases, pero la configuración final no lo usa. Los avisos no obligan a una revisión humana.

## 3. Privacidad

### ¿Se utilizan datos personales o sensibles?

El dataset es simulado. Los correos reales, remitentes, adjuntos y consultas a Redmine pueden incluir nombres, contactos, contraseñas u otros datos sensibles.

### ¿Cómo se protege la privacidad de los usuarios?

El nodo **Limpiar firma y datos** de n8n quita firmas y redacta datos del asunto y cuerpo **antes de enviarlos a NexpAPI y OpenAI**. Usa patrones: puede omitir información y no anonimiza adjuntos ni respuestas de herramientas. El ticket usa el asunto y cuerpo limpios. El original puede quedar en la ejecución de n8n; los adjuntos y el contacto del solicitante se conservan en Redmine.

NexpAPI exige `X-API-Key`, funciona en la red Docker y no publica el puerto 8000. Las claves quedan fuera de Git. Streamlit no llama a OpenAI; su historial SQLite guarda textos y se accede con un enlace privado, sin autenticación de usuarios. Las descargas también pueden contener información sensible.

### Cumplimiento con regulaciones (GDPR, CCPA, etc.)

No se ha auditado ni demostrado cumplimiento de GDPR, CCPA u otras normas. Antes de usar datos personales deben revisarse las obligaciones aplicables, los accesos, el transporte, la retención y los proveedores externos. Limpiar el texto no acredita cumplimiento.

## 4. Transparencia y explicabilidad

### ¿El modelo es interpretable?

TF-IDF y la SVM lineal permiten inspeccionar términos asociados a cada categoría mediante sus coeficientes. Esto no explica por completo cada predicción ni significa que el modelo entienda el correo.

### ¿Los usuarios entienden cómo funciona?

**Acerca de** describe el modelo, sus parámetros, métricas y límites. Se muestran categoría, confianza y probabilidades. Python fija la categoría; OpenAI prepara el análisis y propone prioridad, tipo y proyecto. Una confianza alta puede ser incorrecta.

### Técnicas de explicabilidad implementadas (SHAP, LIME, etc.)

Se revisan coeficientes y términos con `top_terms`. **No se implementaron SHAP ni LIME**. Los gráficos de hiperparámetros explican cambios de rendimiento, no correos individuales.

## 5. Impacto social

### ¿Qué impacto positivo puede tener el proyecto?

Puede reducir tareas de lectura y registro, ordenar la derivación y facilitar el seguimiento en Redmine. Todavía no se midieron ahorro de tiempo ni satisfacción.

### ¿Qué impactos negativos podrían surgir?

Los errores pueden retrasar solicitudes, asignarlas mal o exponer datos. También hay riesgo de confiar demasiado en el resumen o la predicción. No debe decidir por sí solo cierres, accesos o incidentes críticos.

### ¿Quiénes se benefician? ¿Quiénes podrían ser perjudicados?

Se pueden beneficiar mesa de ayuda, técnicos, supervisores y solicitantes. Pueden resultar perjudicados quienes reciban una mala derivación, presenten casos poco comunes o tengan datos personales en el contenido procesado.

## 6. Responsabilidad

### ¿Quién es responsable si el modelo falla?

Soporte responde por la atención y corrección del ticket; el equipo técnico mantiene modelo e integración. **María Quito Castillo**, líder del proyecto y desarrolladora full stack, coordina las correcciones. Faltan los nombres de los demás responsables.

### ¿Qué mecanismos de accountability existen?

Git, las configuraciones, hashes, reportes y ejecuciones de n8n permiten investigar fallos. El flujo valida los datos de Redmine; si Python no devuelve una categoría válida, deriva a revisión sin crear el ticket. No hay aprobación humana obligatoria por ticket ni monitoreo automático de deriva.

### Plan de monitoreo y actualización del modelo

**Plan propuesto; todavía no es una rutina periódica implementada:**

1. Revisar semanalmente una muestra de tickets, errores y avisos de baja confianza; registrar la versión y la corrección humana.
2. Separar fallos del modelo de problemas de integración o asignación y derivarlos a soporte o desarrollo.
3. Preparar datos nuevos autorizados y etiquetados por personas, con un conjunto de evaluación separado del entrenamiento.
4. Comparar F1 macro, accuracy, métricas por categoría y baseline antes de aprobar una actualización.
5. Coordinar la aprobación con la líder del proyecto y soporte; conservar el modelo y la configuración anteriores para poder revertir.
## 7. Uso dual y mal uso

### ¿Podría el modelo usarse con fines maliciosos?

Podría usarse para desviar solicitudes, restar importancia a reclamos o vigilar a trabajadores. También pueden incluirse instrucciones maliciosas en correos o adjuntos para intentar manipular al agente. Estos usos no forman parte del objetivo del proyecto.

### ¿Qué salvaguardas se han implementado?

El prompt trata los correos y adjuntos como contenido no confiable y prohíbe seguir instrucciones que cambien sus reglas. Las herramientas del agente solo consultan Redmine por GET; el código fija la categoría Python y valida proyecto, tipo, categoría y responsable antes de crear el ticket. Además, n8n limpia firmas y datos sensibles del texto antes de enviarlo al clasificador y a OpenAI. Estos controles no garantizan evitar toda manipulación o filtración.

### Limitaciones de uso claramente documentadas

El sistema apoya la atención de soporte TI. No debe usarse para sancionar personas, ocultar reclamos, conceder o revocar accesos ni cerrar solicitudes automáticamente. La limpieza no autoriza a enviar secretos o adjuntos confidenciales al agente.

## 8. Limitaciones reconocidas

### ¿En qué casos NO debe usarse el modelo?

No debe ser el único criterio en incidentes críticos, decisiones de seguridad, permisos o sanciones. Tampoco debe asumirse que funciona igual fuera del soporte TI o con idiomas distintos del español. No se deben cargar modelos `.pkl` de origen desconocido, porque pueden ejecutar código.

### ¿Qué advertencias deben darse a los usuarios?

La categoría y la confianza pueden ser incorrectas; una probabilidad alta no garantiza un acierto. Los datos de entrenamiento son simulados y las métricas no prueban el rendimiento con correos reales. Los avisos de revisión requieren atención del equipo: no obligan automáticamente a una aprobación humana. Los originales y el historial pueden conservar datos sensibles, y los adjuntos no se anonimizan.

### Casos límite donde el modelo no es confiable

Correos muy breves, ambiguos, con varias solicitudes, vocabulario desconocido, otros idiomas o información importante solo en adjuntos. El clasificador recibe título y cuerpo, no interpreta los archivos. También puede confundir una consulta de capacitación con un fallo de aplicación o un problema de permisos con uno de software. En estos casos debe revisarse el correo completo y corregirse la clasificación si corresponde.
