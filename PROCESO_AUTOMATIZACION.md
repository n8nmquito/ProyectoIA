# Proceso de automatización entregado

El diseño completo está en [arquitectura](python/docs/arquitectura.md) y los límites de uso en [consideraciones éticas](python/docs/consideraciones_eticas.md).

## Recorrido actual

1. n8n recibe el correo por IMAP, normaliza los campos y conserva los originales y adjuntos.
2. El nodo **Limpiar firma y datos** ejecuta JavaScript dentro de n8n y redacta datos sensibles del asunto y cuerpo.
3. **Consultar API - Modelo 300** envía ese texto a `http://nexpapi:8000/predict`. Python devuelve la categoría final, confianza y probabilidades.
4. **Unir correo y predicción** recupera el contexto limpio y los adjuntos. El selector valida la respuesta y prepara los archivos permitidos para el agente.
5. OpenAI decide si es una solicitud de soporte, resume y propone prioridad, tipo y proyecto consultando catálogos de Redmine. Recibe la categoría de Python y no puede sustituirla.
6. Si corresponde crear el ticket, **Aplicar categoría Python** fija esa categoría y marca revisión cuando hay baja confianza o desacuerdo.
7. El código resuelve `tipo_ticket` por nombre, comprueba proyecto y categoría, y busca el responsable configurado. Valida membresía y rol antes de asignarlo.
8. Recupera y sube los adjuntos originales, crea el ticket en Redmine y prepara el aviso al remitente.

Si falla la limpieza, la API o la validación de la predicción, el flujo invoca **Revisión y aviso - Subflujo**, que registra la revisión y prepara el aviso según los filtros existentes. No envía el correo al agente ni crea un ticket por esa ruta. Un proyecto, tipo o categoría inválidos también bloquean el alta.

Las herramientas del agente son GET. La creación y asignación posteriores son automáticas tras los controles, sin aprobación humana obligatoria. La baja confianza marca revisión, pero no bloquea por sí sola el ticket. El sistema no concede permisos ni resuelve incidentes.

## Plantilla vigente

Importar [correo-ia-redmine-python300.json](workflows/correo-ia-redmine-python300.json), la plantilla actual de **41 nodos**, desactivada y sin credenciales. Importar primero el [subflujo de revisión y aviso](workflows/revision-aviso-error.json) y seleccionarlo en el nodo **Revisión y aviso - Subflujo**. Consultar la [guía de configuración](workflows/GUIA_CONFIGURACION.md) antes de publicarla.

`workflows/correo-ia-redmine.json` conserva una versión histórica de 47 nodos. No representa la política actual de categoría final y limpieza; se mantiene como referencia de etapas anteriores.

## Pruebas y resultados

- **Verificación actual:** 96 pruebas Python aprobadas, más las suites JavaScript. La ejecución aislada n8n **28845** comprobó dos correos ficticios, limpieza local, NexpAPI y conservación de adjuntos sin crear tickets ni enviar correos; se archivó al terminar.
- **Evidencia histórica:** la prueba inicial de 24 correos creó 20 tickets y bloqueó cuatro tipos. Tras corregir la resolución por nombre, las ejecuciones **28517–28520** crearon los tickets DEMO **40–43**, sin confirmaciones. Los registros están en [resultados iniciales](python/results/n8n_produccion/resultados.json) y [regresión de tipos](python/results/n8n_produccion/regresion_tipo_ticket.json); no equivalen a una prueba nueva del flujo actual.
- **Modelos:** los ocho archivos entregados y sus hashes están en [models](python/models/README.md). Las métricas de referencia y del portal reentrenado se conservan por separado. Los 25 correos son pruebas funcionales y no proporcionan accuracy o F1 sin etiquetas esperadas revisadas.

Un estado `success` de n8n puede incluir un rechazo controlado. Antes de reintentar, comprobar si Redmine ya creó el ticket; no hay una garantía global de deduplicación.

## Privacidad y límites

El asunto y cuerpo llegan limpios a NexpAPI y OpenAI, pero la redacción por patrones puede omitir datos. Los adjuntos seleccionados y las respuestas de herramientas no se anonimizan. Los originales permanecen en n8n y Redmine.

El corpus simulado, los datasets y los modelos entregados están versionados en Git. Las claves y las copias privadas del despliegue se mantienen aparte. No se ha demostrado cumplimiento normativo ni generalización a correos reales; las advertencias y el seguimiento se detallan en la documentación ética.
