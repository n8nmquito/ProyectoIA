# Configuración del flujo integrado

## Plantilla y servicios

Si vas a importar los archivos agregados en `n8n/`, consulta la [guía de exportaciones](../n8n/README.md). Conservan las referencias a las credenciales de origen, que debes revisar en tu instalación.

Usar [correo-ia-redmine-python300.json](correo-ia-redmine-python300.json), la plantilla vigente de 41 nodos. `correo-ia-redmine.json` es una referencia histórica con otra lógica de clasificación.

| Nodo o servicio | Configuración |
|---|---|
| Leer buzón IMAP | Credencial del buzón, host/puerto/TLS del proveedor, INBOX y formato Resolved |
| Limpiar firma y datos | Nodo Code JavaScript local; no requiere servicio ni credencial adicional |
| Consultar API - Modelo 300 | `POST http://nexpapi:8000/predict`; Header Auth con nombre `X-API-Key` |
| Agente OpenAI | Credencial del proveedor, modelo `gpt-4.1-mini` y límite de salida de 4.000 tokens |
| Herramientas y nodos Redmine | Header Auth con nombre `X-Redmine-API-Key` |
| Avisos de correo | Credencial SMTP y remitente autorizado |

Las claves se administran en n8n y en los archivos privados del servicio. `X-API-Key` debe coincidir con `CLASSIFIER_API_KEY` del `.env` de NexpAPI. No escribir secretos en el flujo exportado ni en Git.

NexpAPI comparte la red Docker de n8n y no publica el puerto 8000. El host interno es `nexpapi`, no `localhost`. Consultar [NexpAPI](../nexpapi/README.md) y [operación del despliegue](../python/deploy/DESPLIEGUE_REALIZADO.md).

En **Leer buzón IMAP → Options**, configurar **Force Reconnect Every Minutes = 1**. El nodo escucha los correos nuevos y renueva la conexión cada minuto para volver a comprobar el buzón. Mantener **Fetch Only New Emails** activado y la regla `["UNSEEN"]`. Es una reconexión del disparador IMAP, no un horario de ejecución: si no hay correos nuevos, no inicia el resto del flujo.

### URL interna de Redmine y acceso del usuario

En los nodos de n8n se usa **`http://redmine:3000`** para consultar Redmine y crear tickets. Esa dirección funciona dentro de la red Docker **`correo-tickets_automatizacion`**.

Para entrar desde el navegador, se usa **[http://185.208.207.203:3000/](http://185.208.207.203:3000/)**. Los correos de confirmación también deben llevar esta dirección; por ejemplo, `http://185.208.207.203:3000/issues/54`.

En los nodos, conserva `redmine` como servidor. Si lo cambias por `localhost`, n8n intentará conectarse a sí mismo. Consulta el [manual de usuario](../python/docs/manual_usuario.md#8-direcciones-de-acceso-y-red-interna) para ver qué dirección usar.

## Credenciales de n8n: para qué sirven y cómo se usan

Los nombres siguientes corresponden a la lista de credenciales de la instalación. Cada credencial guarda los datos de acceso de un servicio; los nodos que la seleccionan pueden utilizarla sin escribir la clave en el código. Las plantillas exportadas no incluyen esas credenciales: hay que seleccionarlas nuevamente al importar.

### 1. Clasificador Python 300 - API interna

- **Tipo:** Header Auth.
- **Para qué sirve:** autorizar las consultas al clasificador Python de 300 correos que expone NexpAPI. Devuelve categoría, confianza y probabilidades.
- **Qué configurar:** nombre del encabezado `X-API-Key` y, como valor, la misma clave que `CLASSIFIER_API_KEY` del `.env` privado de NexpAPI.
- **Cómo se usa:** seleccionar esta credencial en **Consultar API - Modelo 300**, con autenticación Header Auth, método `POST` y URL `http://nexpapi:8000/predict`. El cuerpo JSON contiene `titulo` y `cuerpo` limpios. n8n agrega la clave al encabezado de la petición.

### 2. OpenAI account

- **Tipo:** OpenAI.
- **Para qué sirve:** permitir que el agente analice la solicitud, genere el resumen y proponga prioridad, tipo y proyecto. La categoría final sigue siendo la de Python.
- **Qué configurar:** la API key de OpenAI del proyecto autorizado para ejecutar el agente.
- **Cómo se usa:** seleccionar la credencial en **OpenAI - Cargar API key**, conectado a **Agente IA - Analizar solicitud**. El modelo configurado es `gpt-4.1-mini`. Esta conexión utiliza texto limpio, adjuntos seleccionados y contexto de las herramientas; no entrena el clasificador Python.

### 3. Mquito - Seguimiento de tickets PostgreSQL

- **Tipo:** Postgres.
- **Para qué sirve:** guardar el último estado observado de cada ticket y los avisos pendientes, enviados o fallidos. Permite reconocer cambios de estado y evitar repetir una misma transición en el flujo de notificaciones.
- **Qué configurar:** host interno `postgres`, puerto `5432`, base `n8n`, usuario dedicado `mquito_ticket_notify` y su contraseña privada. El esquema utilizado es `ticket_notify`.
- **Cómo se usa:** asignarla a los nodos PostgreSQL del flujo **Mquito | Avisos de cambios de estado Redmine**: **Comparar y registrar cambios**, **Reservar avisos pendientes**, **Registrar envío aceptado** y **Registrar fallo de envío**. Esta cuenta necesita los permisos de lectura, escritura y ejecución previstos por el script de instalación; una cuenta de solo lectura no sirve para ese seguimiento.
- **Referencia:** [configuración del seguimiento](status-notifications/README.md#configuración).

### 4. Gmail soporte - Notificaciones SMTP

- **Tipo:** SMTP.
- **Para qué sirve:** enviar los avisos de ticket creado, correo omitido, error de procesamiento y cambios de estado al solicitante.
- **Qué configurar:** servidor `smtp.gmail.com`, puerto `465` con TLS, usuario del buzón y la credencial de acceso SMTP admitida por esa cuenta; el remitente debe estar autorizado.
- **Cómo se usa:** seleccionarla en **Notificar - Ticket creado**, **Notificar - Correo omitido**, **Notificar - Error de procesamiento** y **Notificar cambio al solicitante**. Los filtros del flujo deciden si corresponde enviar el mensaje. SMTP envía correos; la lectura del buzón utiliza IMAP.

### 5. Mquito ML - PostgreSQL solo lectura

- **Tipo:** Postgres.
- **Para qué sirve:** por su nombre y los antecedentes del despliegue, corresponde al mecanismo anterior de clasificación basado en PostgreSQL. Su configuración y sus permisos efectivos no se pueden comprobar desde la captura.
- **Qué configurar si se conserva para consultas:** host, puerto, base, usuario y contraseña de la cuenta con permisos de lectura sobre los objetos necesarios. El nombre «solo lectura» no impone permisos: estos se conceden en PostgreSQL.
- **Cómo se usa actualmente:** las plantillas vigentes del clasificador y de avisos no contienen nodos de clasificación que la necesiten. El modelo actual se consulta mediante **Clasificador Python 300 - API interna**. Antes de reutilizarla, revisar sus conexiones en n8n y los permisos de la cuenta; no asignarla a los nodos que registran notificaciones.

### 6. Header Auth account

- **Tipo:** Header Auth.
- **Para qué sirve en este proyecto:** autenticar las consultas y operaciones sobre Redmine, incluidas lectura de catálogos, validación de responsables, subida de adjuntos y creación de tickets.
- **Qué configurar:** nombre del encabezado `X-Redmine-API-Key` y, como valor, la API key de la cuenta de integración de Redmine. Verificar ese encabezado al abrir la credencial, ya que su nombre genérico no identifica el servicio por sí solo.
- **Cómo se usa:** seleccionarla en las herramientas y nodos HTTP de Redmine, como **Consultar proyectos**, **Verificar proyecto propuesto**, **Subir adjunto a Redmine**, **Crear ticket en Redmine** y **Consultar tickets de Redmine** del flujo de seguimiento. Las operaciones permitidas dependen de los permisos de la cuenta en Redmine.

### 7. IMAP account

- **Tipo:** IMAP.
- **Para qué sirve:** recibir los correos de soporte y sus adjuntos para iniciar la automatización.
- **Qué configurar:** servidor IMAP del proveedor, puerto, TLS, usuario del buzón y su credencial de acceso. Usar los valores admitidos por la cuenta de correo.
- **Cómo se usa:** seleccionarla en **Leer buzón IMAP**; configurar la carpeta `INBOX` y el formato `Resolved` del nodo. El correo recibido pasa luego a normalización y limpieza. Para responder o notificar se usa la credencial SMTP.

### Dónde seleccionarlas

En n8n, abrir **Credentials** para crear o editar la credencial del tipo correspondiente. Después abrir el nodo que la necesita y seleccionarla en su campo de credenciales. En los nodos HTTP, comprobar también el tipo de autenticación y el encabezado del servicio. Los nodos Code de limpieza y preparación no requieren credenciales propias.

Las cantidades de conexiones que aparecen junto a algunas credenciales indican referencias dentro de n8n; no son permisos ni cantidades de solicitudes realizadas. Esta guía identifica su uso según las plantillas del repositorio y la captura, sin inspeccionar los secretos ni la configuración privada de la instalación.

## Entrada, salida y errores

1. **Limpiar firma y datos** quita firmas y redacta datos sensibles del asunto/cuerpo dentro de n8n.
2. **Consultar API - Modelo 300** envía solo `titulo` y `cuerpo` limpios a `/predict`.
3. **Unir correo y predicción** reúne el correo limpio, sus adjuntos y la respuesta.
4. **Seleccionar adjuntos para IA** verifica que la respuesta corresponda a `modelo_clasificador_300`, con 300 muestras, categoría y probabilidades válidas; luego prepara archivos para el agente.
5. El agente omite comandos, código o inventarios aislados sin problema ni solicitud de ayuda. Las solicitudes de acceso, configuración o asistencia siguen siendo válidas sin un error. El agente recibe la categoría Python y analiza el correo. **Preparar ticket - Intaco** fija la categoría Python y construye el ticket en un solo nodo.

Si falla la limpieza, la API o la validación de la respuesta, la ejecución deriva directamente a **Sin análisis IA - Revisión**. No pasa al agente ni crea un ticket con una categoría de respaldo. La descripción de Redmine también usa el asunto y cuerpo limpios. Los adjuntos originales y el contacto del solicitante se conservan; no se anonimizan los archivos.

Cuando el agente decide **omitir**, la rama **Correo omitido** registra que no se creó un ticket y envía al remitente una respuesta con el asunto **Solicitud no válida: correo descartado**. El mensaje explica el descarte y cómo enviar una solicitud de soporte concreta. Un fallo técnico del procesamiento sigue la rama de error; no se presenta como un descarte por contenido.

## Tipo, categoría y responsable

El agente devuelve `tipo_ticket` como **Errores** o **Soporte**. El código consulta los tipos habilitados y obtiene un ID único. Un nombre ausente, ambiguo o no habilitado impide crear el ticket.

Configurar las categorías **Accesos, Aplicaciones, Infraestructura y Otros** con nombres únicos por proyecto. Si una tiene responsable predeterminado, el código lo prioriza y verifica su membresía, rol asignable y permiso `view_issues`. Si esa verificación falla, se detiene el alta para revisión.

Sin responsable configurado, se valida la propuesta del agente. El flujo puede dejar el ticket sin asignar y marcado para revisión si no hay una propuesta válida. Las consultas actuales recuperan hasta 100 miembros: proyectos mayores requieren ampliar la paginación.

## Comprobación antes de publicar

- Reasignar las credenciales a la plantilla vigente, que se exporta desactivada.
- Comprobar que el nodo de limpieza sea Code JavaScript y que la API use `http://nexpapi:8000/predict`.
- Revisar las conexiones de error hacia **Sin análisis IA - Revisión** y la aplicación obligatoria de la categoría Python dentro de **Preparar ticket - Intaco**.
- Ejecutar las pruebas locales indicadas en el [README](README.md#pruebas-y-diagnóstico).
- Para una prueba completa, preparar una copia aislada que sustituya creación de tickets y SMTP por comprobaciones. La rama manual del flujo principal sí puede generar un ticket real.

## Diagnóstico de una ejecución

Abrir **Executions** y revisar los nodos de limpieza, API y validación. Un estado `success` no demuestra que exista un ticket: comprobar **Resultado del ticket** y su ID en Redmine antes de reintentar.

La señal de revisión no obliga a una aprobación humana. Las validaciones comprueban formatos y catálogos, no la veracidad completa del resumen. OpenAI puede recibir texto limpio, adjuntos seleccionados y respuestas de herramientas; la limpieza no equivale a anonimización completa.
