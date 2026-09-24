# Guía de configuración del flujo de soporte

Este flujo lee un correo, analiza la solicitud con Gemini, consulta los proyectos y responsables de Redmine y crea un ticket con sus adjuntos.

[Abrir el flujo en n8n](http://185.208.207.203:5678/workflow/opxBwpGpRDrbQeHn) · [Abrir Redmine](http://185.208.207.203:3000)

La guía describe la copia del flujo guardada en este repositorio. Las credenciales se cargan en n8n y no vienen incluidas en el JSON importable.

## 1. Lo que necesitás configurar

| Configuración | Dónde se carga | Para qué sirve |
|---|---|---|
| Acceso al correo | **Leer buzón IMAP** → credencial IMAP | Leer mensajes y descargar archivos. |
| Clave de Gemini | **Google Gemini Chat Model** → credencial | Analizar el correo y consultar las herramientas. |
| Clave API de Redmine | Credencial **Header Auth** en todos los nodos HTTP de Redmine | Consultar proyectos, subir archivos y crear tickets. |
| Proyectos, tipos de ticket y miembros | En Redmine | Darle al agente opciones reales para clasificar y asignar. |

Para modificar un nodo, abrilo con doble clic. **Parameters** contiene su configuración; **Settings** incluye opciones de errores y ejecución. Los nombres pueden variar según el idioma de n8n.

Un campo con `{{ ... }}` es una **expresión**: obtiene un valor durante la ejecución. No lo reemplaces por un ejemplo fijo. En los nodos **Code**, los límites y reglas se editan dentro del código.

## 2. Leer buzón IMAP

Este es el disparador automático. Se conecta al buzón para recibir correos nuevos.

| Parámetro | Valor o configuración | Explicación |
|---|---|---|
| Credential | Credencial IMAP del buzón | Incluye host, usuario, contraseña, puerto y TLS. |
| Host | El servidor IMAP de tu proveedor | No es la dirección de n8n ni la de Redmine. |
| User | La cuenta del buzón | Normalmente el correo completo. |
| Password | Contraseña admitida por el proveedor | Algunos proveedores requieren contraseña de aplicación u otro método de acceso. |
| Port / TLS | Según el proveedor; habitualmente `993` con TLS | Estos valores pertenecen a la conexión al correo. |
| Mailbox | `INBOX`, valor predeterminado | Carpeta que escucha el nodo. |
| Format | `Resolved` | Entrega el contenido procesado y los adjuntos como datos binarios. |
| Custom Email Rules | `["UNSEEN"]` | Filtra mensajes no leídos. |
| Action / Post Process | `Nothing` | El flujo no marca automáticamente el correo como leído. |
| Track Last Message ID | Activado | Lleva seguimiento del último mensaje procesado por el disparador. |
| Force Reconnect | `60` minutos | Renueva la conexión; no es un intervalo de consulta de 60 segundos. |

El seguimiento del último mensaje **no reemplaza un control permanente de duplicados**. Evitá reprocesar la misma ejecución sin revisar si ya creó un ticket.

## 3. Normalizar correo y seleccionar adjuntos

**Normalizar correo** prepara asunto, remitente, fecha y texto. Si no hay texto plano, intenta obtenerlo del HTML. Conserva los adjuntos originales para enviarlos después a Redmine.

| Parámetro en el código | Valor actual | Qué limita |
|---|---|---|
| Longitud del texto | `16000` caracteres | Texto del correo que se prepara para el análisis. |
| Longitud del asunto | `255` caracteres | Asunto normalizado. |

**Seleccionar adjuntos para IA** decide qué archivos recibe Gemini:

| Variable | Valor actual | Significado |
|---|---|---|
| `supported` | PNG, JPEG, WebP y PDF | Formatos seleccionados para análisis. |
| `maxFiles` | `4` | Cantidad máxima de archivos enviados a la IA por correo. |
| `maxFile` | `4 * 1024 * 1024` | Hasta 4 MiB por archivo. |
| `maxTotal` | `8 * 1024 * 1024` | Hasta 8 MiB entre todos los archivos seleccionados. |

Por ejemplo, un PDF de 2 MiB puede enviarse a Gemini. Un ZIP se conserva para adjuntarlo al ticket, sin analizarlo ni descomprimirlo.

**Todos los originales se intentan adjuntar a Redmine**, incluso los que no recibe la IA. Los límites anteriores son del análisis; Redmine tiene sus propios límites de subida. Agregar un formato a `supported` no garantiza que el modelo pueda interpretarlo.

## 4. Modelo Gemini y agente IA

### Google Gemini Chat Model

Seleccioná la credencial de Gemini y revisá el campo **Model**. El export actual no fija un nombre de modelo: utiliza el predeterminado de la versión instalada del nodo. Elegí explícitamente uno disponible en tu cuenta si querés mantener esa elección.

El antiguo nodo de OpenAI está desconectado y no participa en el flujo.

### Agente IA - Analizar solicitud

| Parámetro | Valor actual | Para qué sirve |
|---|---|---|
| Prompt Type | `Define` | El flujo construye el mensaje que recibe el agente. |
| Text | Expresión con `asunto`, `texto` y `adjuntos` | Envía los datos del correo actual. |
| System Message | Instrucciones de soporte y asignación | Define las categorías, prioridades y reglas para elegir responsable. |
| Require Specific Output Format | Activado | Obliga a devolver los campos esperados por el siguiente nodo. |
| Max Iterations | `12` | Máximo de ciclos de razonamiento y consultas a herramientas por ejecución del agente. |
| Automatically Passthrough Binary Images | Activado | Permite pasar las imágenes seleccionadas al modelo. |
| Automatically Passthrough Binary PDFs | Activado | Permite pasar los PDF seleccionados al modelo. |
| Force Tool Call on First Iteration | Activado | Exige que el agente comience consultando una herramienta. |
| On Error | `Continue (using error output)` | Envía los errores a la rama de revisión. |

Para cambiar los criterios de clasificación o asignación, editá **System Message**. Por ejemplo, podés ajustar qué roles deberían atender problemas de accesos. Las instrucciones actuales piden consultar datos reales y no inventar usuarios, disponibilidad ni carga de trabajo.

### Formato del análisis

Este nodo define la estructura de la respuesta. Los campos principales son:

| Campo | Contenido esperado |
|---|---|
| `resumen`, `descripcion` | Resumen y detalle de la solicitud. |
| `categoria` | `aplicaciones`, `infraestructura`, `accesos` u `otros`. Se incorpora al texto del ticket; no configura una categoría nativa de Redmine. |
| `prioridad` | `baja`, `normal`, `alta` o `urgente`. |
| `requiere_revision`, `datos_faltantes` | Indican si una persona debe revisar o completar información. |
| `project_id` | ID del proyecto de Redmine. |
| `tracker_id` | ID del tipo de ticket; no es el rol del usuario. |
| `assigned_to_id` | ID del usuario propuesto como responsable. |
| `membership_id` | ID de la membresía que vincula al usuario con el proyecto. |
| `role_id` | ID del rol de esa membresía. |
| `motivo_asignacion` | Explicación de la elección. |

Usuario, membresía y rol se devuelven como `0` cuando no hay candidato válido. Proyecto y tipo de ticket deben ser IDs positivos existentes. Si cambiás este formato, también necesitás adaptar el código que procesa la respuesta.

## 5. Dónde ingresar X-Redmine-API-Key

1. En Redmine, abrí **Mi cuenta** y obtené la clave de acceso a la API. La API REST debe estar habilitada en la administración.
2. En n8n, abrí un nodo como **Crear ticket en Redmine**.
3. En **Authentication**, seleccioná `Generic Credential Type`.
4. En **Generic Auth Type**, seleccioná `Header Auth`.
5. Creá o editá la credencial con estos campos:

   | Campo de la credencial | Valor |
   |---|---|
   | Name | `X-Redmine-API-Key` |
   | Value | Tu clave API de Redmine |

6. Seleccioná **esa misma credencial** en las cinco herramientas del agente, los tres nodos HTTP de verificación, **Subir adjunto a Redmine** y **Crear ticket en Redmine**.

La clave va en la **credencial**, no en la URL ni en el JSON del ticket. La cuenta dueña de la clave debe tener permisos para consultar los proyectos y sus miembros, crear tickets, adjuntar archivos y asignar responsables donde corresponda.

### Herramientas HTTP del agente

Todas usan `GET`, la misma credencial y la dirección interna `http://redmine:3000`.

| Nodo | Ruta de la API | Qué obtiene |
|---|---|---|
| Consultar proyectos | `/projects.json` | Proyectos visibles para la cuenta de integración. |
| Consultar miembros del proyecto | `/projects/{project_id}/memberships.json` | Usuarios del proyecto, membresías y roles. |
| Consultar proyecto y tipos | `/projects/{project_id}.json?include=trackers` | Proyecto y tipos de ticket disponibles. |
| Consultar rol | `/roles/{role_id}.json` | Si el rol permite asignación y qué permisos tiene. |
| Consultar cuenta API | `/users/current.json` | Cuenta que utiliza la integración. |

Los IDs se completan mediante expresiones `$fromAI(...)` a partir de las consultas del agente. Los listados usan `limit=100` y `offset` para paginar: son registros por página, no tickets a crear. El tiempo de espera por consulta es `30000` milisegundos, es decir, 30 segundos.

Si movés n8n fuera de la red Docker compartida, reemplazá `http://redmine:3000` en **todos** los nodos HTTP por una dirección accesible desde el nuevo servidor.

## 6. Preparar y validar la asignación

**Preparar ticket - Intaco** conserva su nombre original, pero utiliza el proyecto propuesto por el agente. Convierte la prioridad a los IDs configurados en el código:

| Prioridad del análisis | ID de prioridad en Redmine |
|---|---|
| Baja | `1` |
| Normal | `2` |
| Alta | `3` |
| Urgente | `4` |

Si cambiás las prioridades en Redmine o usás otra instalación, verificá que esos IDs coincidan.

Antes de crear el ticket, otros nodos vuelven a consultar la API:

- **Verificar proyecto propuesto** y **Validar proyecto y tipo** comprueban que el proyecto esté activo y admita el tipo de ticket. Si no es válido, se detiene el alta.
- **¿Propone responsable?** revisa si existe un usuario propuesto.
- **Verificar membresía elegida**, **Verificar rol asignable** y **Validar responsable real** comprueban que el usuario pertenezca al proyecto y tenga el rol indicado, con `assignable=true` y permiso `view_issues`.

Si el responsable no pasa la validación, el ticket se prepara para revisión sin enviar `assigned_to_id`. Una asignación predeterminada configurada en Redmine podría aplicarse igualmente. Esta versión propone usuarios individuales, no grupos.

Los nodos HTTP de verificación usan **Include Response Headers and Status** y **Never Error** para entregar el estado HTTP al código de validación. Esto permite evaluar el error; no significa aceptar una respuesta inválida.

### Cuando la IA falla

**Sin análisis IA - Revisión** prepara una solicitud con prioridad Normal y marca `[REVISAR]`, conservando correo y adjuntos. Su configuración de respaldo usa **proyecto `1` y tipo de ticket `3`**. El mensaje de sistema también menciona **Intaco (`1`)** como proyecto de revisión ante ambigüedad.

Si cambiás de proyecto de respaldo, actualizá esos valores en el nodo de revisión y en el mensaje de sistema. La validación posterior sigue aplicando: un fallo de permisos, un proyecto inválido o un error de subida puede impedir crear el ticket.

## 7. Subir adjuntos y crear el ticket

**Recuperar adjuntos originales** reúne nuevamente los archivos del correo. **¿Hay adjuntos?** elige la ruta; **Separar adjuntos** prepara una carga por archivo.

| Parámetro | Subir adjunto a Redmine | Crear ticket en Redmine |
|---|---|---|
| Method | `POST` | `POST` |
| URL | `http://redmine:3000/uploads.json` | `http://redmine:3000/issues.json` |
| Authentication | Credencial Header Auth de Redmine | La misma credencial |
| Body | `n8n Binary File`, campo `data` | JSON, expresión `{{ JSON.stringify($json) }}` |
| Parámetro adicional | Query `filename` con el nombre del archivo | El objeto `issue` contiene los datos del ticket |
| Content-Type | `application/octet-stream` | JSON |
| Timeout | `60000` ms = 60 segundos | `30000` ms = 30 segundos |

**Reunir tokens de adjuntos** coloca en `issue.uploads` los tokens que devuelve Redmine. No son contraseñas que tengas que ingresar: se generan al subir cada archivo.

Se crea **un ticket por correo**, con sus archivos. Si una subida falla, el flujo se detiene antes de crear ese ticket. No hay reintentos automáticos de creación: antes de reejecutar una solicitud que terminó con timeout, verificá si Redmine ya la recibió.

**Resultado del ticket** devuelve el ID, asunto y enlace del ticket creado.

## 8. Prueba manual y funcionamiento automático

### Probar

1. Guardá los cambios y seleccioná las credenciales necesarias.
2. Ejecutá desde **Prueba manual**. **Correo de ejemplo** genera datos ficticios y adjuntos de prueba.
3. Revisá **Resultado del ticket** y abrí el enlace para comprobar descripción, responsable y archivos.

**La prueba manual consume la API de Gemini y crea un ticket real de demostración en Redmine.** No envía un correo de respuesta al remitente.

### Recibir correos automáticamente

1. Verificá la conexión y configuración de **Leer buzón IMAP**.
2. Guardá y **publicá/activá** el flujo, según el botón que muestre tu versión de n8n.
3. Enviá un correo nuevo al buzón configurado.
4. Abrí **Executions** para comprobar el resultado.

**No necesitás deshabilitar Prueba manual.** Esa entrada solo se ejecuta cuando la invocás. Para la recepción automática, n8n debe seguir funcionando y el flujo debe estar publicado/activo; tener abierto el editor no lo activa.

El flujo guarda ejecuciones correctas, fallidas y manuales. Su tiempo máximo total es **300 segundos** y la zona horaria configurada es `America/Argentina/Buenos_Aires`.

## 9. Cómo localizar un error

En **Executions**, abrí la ejecución y seleccioná el nodo que falló. Revisá **Input**, **Output** y el mensaje de error. Si se usó la rama de respaldo, la ejecución puede terminar correctamente y aun así crear un ticket `[REVISAR]`.

| Síntoma | Dónde revisar | Qué comprobar |
|---|---|---|
| No se inicia al llegar un correo | Leer buzón IMAP y estado del flujo | Publicación/activación, conexión, carpeta y condición de no leído. |
| Gemini devuelve `429` o `503` | Agente y modelo Gemini | Cuota o disponibilidad del servicio; comprobar si siguió por revisión. |
| La respuesta no tiene el formato esperado | Formato del análisis | Campos requeridos y valores admitidos. |
| Redmine devuelve `401` | Credencial Header Auth | Nombre exacto del encabezado y clave API. |
| Redmine devuelve `403` | Nodo HTTP que falló | Permisos de la cuenta en ese proyecto. |
| Proyecto o tipo inválido | Validar proyecto y tipo | IDs existentes, proyecto activo y tipo habilitado. |
| Ticket sin responsable propuesto | Validar responsable real | Membresía, rol, permisos y motivo de revisión en la descripción. |
| Falla un adjunto | Subir adjunto a Redmine | Tamaño permitido, restricciones y respuesta del servidor. |
| Redmine devuelve `422` al crear | Crear ticket en Redmine | Campos obligatorios o personalizados que exige el proyecto. |

## 10. Alcance de las pruebas realizadas

Se probó la creación con Gemini y adjuntos, y la rama de revisión ante un PDF ilegible. También se verificaron las consultas del agente a Redmine y la validación/asignación posterior con una propuesta simulada.

La selección autónoma completa del responsable quedó pendiente de una prueba sin errores de disponibilidad de Gemini. También falta verificar de punta a punta un correo real recibido por IMAP. El flujo todavía no incorpora deduplicación persistente ni seguimiento de respuestas a tickets existentes.

Para detalles técnicos y el JSON importable, consultá [la documentación del flujo](README.md).
