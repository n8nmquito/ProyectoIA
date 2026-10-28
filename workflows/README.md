# Correo → NexpAPI → OpenAI → Redmine

El flujo principal utiliza el modelo de 300 correos de **NexpAPI** y el agente **OpenAI**. Python determina la categoría final; el agente analiza la solicitud y consulta Redmine. La API se consulta en `http://nexpapi:8000/predict` con la credencial Header Auth `X-API-Key`.

## Recorrido actual

Correo → normalizar → limpiar firmas y datos con JavaScript en n8n → consultar NexpAPI → unir correo limpio y predicción → validar respuesta y seleccionar adjuntos → agente OpenAI → decidir relevancia → aplicar categoría Python → validar proyecto, tipo y categoría → resolver y validar responsable → subir originales → crear ticket → preparar confirmación.

Si la limpieza o la API fallan, o la predicción no es válida, se deriva directamente a **Revisión y aviso - Subflujo** antes de llegar al agente. La baja confianza o el desacuerdo del agente marcan revisión y conservan la categoría Python. La creación no requiere aprobación humana obligatoria.

El responsable configurado en la categoría de Redmine tiene prioridad. Se consulta su membresía y rol asignable; si no puede verificarse, se detiene el alta. Si no hay responsable configurado, se valida la propuesta del agente o se deja el ticket sin asignar para revisión. `tipo_ticket` se resuelve por nombre contra el catálogo del proyecto: no se inventan IDs.

## Qué archivo importar

| Archivo | Estado y uso |
|---|---|
| [correo-ia-redmine-python300.json](correo-ia-redmine-python300.json) | **Plantilla vigente: 41 nodos**, limpieza local y categoría Python obligatoria. Usar para nuevas instalaciones |
| [revision-aviso-error.json](revision-aviso-error.json) | **Subflujo vigente: 6 nodos**, recibe el contexto y centraliza revisión, preparación y envío del aviso |
| [correo-ia-redmine.json](correo-ia-redmine.json) | **Referencia histórica: 47 nodos**. Conserva la lógica anterior de comparación y no reproduce el flujo actual |

Las exportaciones están desactivadas y sin credenciales. Importa primero el subflujo, asigna su credencial SMTP y selecciónalo en el nodo de llamada del principal; al importar en otra instancia, su ID puede cambiar. Reasigna las credenciales antes de publicar la plantilla vigente y guarda la versión activa antes de modificarla. Son versiones diferentes, no copias intercambiables.

Consultar [configuración](GUIA_CONFIGURACION.md), [NexpAPI](../nexpapi/README.md) y [arquitectura](../python/docs/arquitectura.md). Las claves permanecen en el `.env` del servicio y en las credenciales cifradas de n8n.

## Limpieza y adjuntos

El nodo **Limpiar firma y datos** ejecuta [limpiar-correo.js](nodes/limpiar-correo.js) dentro de n8n. Elimina firmas habituales y redacta contactos, IP, enlaces, credenciales y campos personales etiquetados. No llama a un endpoint de limpieza. Si no queda texto útil, deriva a revisión sin usar el original como respaldo.

**Unir correo y predicción** conserva el texto limpio y los adjuntos junto con la respuesta de NexpAPI. El selector comprueba modelo, categoría y probabilidades antes de pasar al agente; no vuelve a clasificar.

El agente puede recibir PNG, JPEG, WebP y PDF: hasta **4 archivos**, **4 MiB por archivo** y **8 MiB en total**. Los originales se conservan para Redmine. La selección y la limpieza de texto no anonimizan adjuntos ni garantizan detectar todos los datos sensibles.

## Pruebas y diagnóstico

Desde la raíz del repositorio, ejecutar sin crear tickets ni enviar correos:

```bash
node workflows/test-error-subflow.cjs
node workflows/test-email-cleaning.cjs
node workflows/test-python-category.cjs
node workflows/status-notifications/test.cjs
```

Las tres primeras suites comprueban el subflujo de errores, la limpieza local y la autoridad de la categoría Python. La última verifica los avisos de cambios de estado.

Estas comprobaciones se conservan para la plantilla histórica y sus componentes:

```bash
node workflows/test-workflow.cjs
node workflows/test-assignment.cjs
node workflows/test-attachments.cjs
```

La ejecución aislada **28845** comprobó NexpAPI y los adjuntos con dos correos ficticios, sin agentes externos, tickets ni SMTP. Las pruebas históricas de 24 correos y la corrección posterior de tipos están registradas en [resultados](../python/results/n8n_produccion/resultados.json) y [regresión](../python/results/n8n_produccion/regresion_tipo_ticket.json).

La rama manual del flujo principal puede crear tickets reales. Un estado `success` puede contener un rechazo controlado: comprobar el ID en Redmine antes de reintentar. El cursor IMAP evita reprocesar mensajes antiguos ya considerados; no sustituye una garantía global de idempotencia.

Ver [consideraciones éticas](../python/docs/consideraciones_eticas.md) para privacidad, revisión y límites de uso.


## Subflujo de revisión y aviso de error

Las **22 rutas de error** del principal llegan a un único nodo **Revisión y aviso - Subflujo**. Este llama a **Mquito | Revisión y aviso de error** y espera su resultado. Dentro del subflujo quedan el registro de revisión, la preparación del aviso, el filtro de notificación, SMTP y la devolución del estado.

Recibe un objeto `context` con `email` (remitente, asunto, message_id y demo), `raw` (from, subject y cabeceras de mensajes automáticos) y `origen` (IDs del flujo y ejecución). El principal prepara esos metadatos con [contexto-error.js](nodes/contexto-error.js); no transfiere el cuerpo ni los adjuntos. Otros flujos del mismo propietario pueden invocarlo mapeando ese contrato.

Los filtros de destinatario y pruebas DEMO se conservan. La salida devuelve `pendiente_revision`, el motivo y los datos del aviso; un fallo SMTP no convierte el caso en procesado correctamente ni crea un ticket. No hay reintentos automáticos de envío.

Las ejecuciones aisladas **28867**, **28870** y **28872** verificaron la llamada real, los avisos omitidos, un envío simulado, un fallo SMTP simulado y un lote mixto. Los diagnósticos se archivaron. **No se enviaron correos reales** en esas pruebas.
