# Flujo de correo y adjuntos → Gemini → Redmine

[**Abrir el flujo en n8n**](http://185.208.207.203:5678/workflow/opxBwpGpRDrbQeHn)

El flujo está guardado **sin activar**. La copia `correo-ia-redmine.json` es
importable y no incluye credenciales. La instancia usa Gemini; el antiguo nodo
OpenAI permanece desconectado y no participa.

## Credenciales

- **Leer buzón IMAP:** usuario, contraseña o contraseña de aplicación, host,
  puerto y TLS. Usa `INBOX` y formato `Resolved` para descargar los adjuntos.
- **Google Gemini Chat Model:** seleccionar una credencial Google Gemini válida.
- **Crear ticket en Redmine** y **Subir adjunto a Redmine:** seleccionar la misma
  credencial **Header Auth**, con **Name = X-Redmine-API-Key** y **Value = clave
  de la API de Redmine**, disponible en Mi cuenta. Las credenciales ya seleccionadas
  en la instancia se conservaron; al importar el JSON hay que reasignarlas.

Los nodos HTTP usan `http://redmine:3000` dentro de Docker. En otra instalación
n8n, cambiar ambas URLs por una dirección accesible desde ese servidor.

## Proceso

```mermaid
flowchart LR
    E[Correo IMAP + adjuntos] --> N[Normalizar y conservar originales]
    N --> S[Seleccionar archivos para IA]
    S --> A[Agente Gemini]
    A -->|Análisis correcto| P[Preparar ticket]
    A -->|Error| F[Marcar para revisión]
    F --> P
    P --> R[Recuperar todos los originales]
    R --> I{¿Hay archivos?}
    I -->|Sí| U[Subir archivos a Redmine]
    U --> T[Reunir tokens por correo]
    T --> C[Crear ticket con adjuntos]
    I -->|No| C
```

- El agente recibe asunto, texto y los archivos seleccionados. El texto se limita
  a 16000 caracteres; se indica en el ticket si fue recortado.
- Se envían a Gemini **PNG, JPEG, WebP y PDF**, con un máximo de **4 archivos**,
  **4 MiB por archivo** y **8 MiB en total**. Estos son límites del flujo,
  editables en **Seleccionar adjuntos para IA**.
- Los demás formatos, los archivos que exceden esos límites y todos los originales
  seleccionados se cargan igualmente en Redmine. No se descomprimen ZIP ni se
  convierten documentos Office. El correo puede contener únicamente adjuntos.
- Si Gemini o el parser fallan, el flujo crea un ticket **[REVISAR]** con el correo
  y los adjuntos originales, prioridad Normal y aviso de análisis no completado.
- Las instrucciones dentro de correos o archivos se tratan como datos; no pueden
  cambiar la URL, las credenciales, el proyecto ni los permisos del flujo.
- Cada archivo se carga en `/uploads.json`; sus tokens se reúnen en el mismo
  ticket, sin crear un ticket por archivo ni mezclar adjuntos de distintos correos.
- Proyecto: **Intaco (ID 1)**. Tipo: **Soporte (ID 3)**. No se asigna un técnico.

La subida está sujeta al límite de tamaño y a las restricciones del servidor
Redmine. Si un archivo es rechazado, el flujo se detiene antes del alta, evitando
crear un ticket que parezca completo con archivos faltantes. Las cargas ya hechas
pueden quedar temporalmente sin asociar a una petición.

## Prueba manual

**Prueba manual → Correo de ejemplo** genera un correo ficticio con:

1. `detalle-error-demo.pdf`, con el código de error ACCESO-403.
2. `imagen-demo.png`, una imagen mínima de prueba.
3. `notas-demo.txt`, que solo se adjunta a Redmine.

Ejecutar esta rama llama a Gemini y crea un ticket real con prefijo `[DEMO]`.
Luego probar con un correo controlado del buzón y publicar/activar el flujo.

## Verificación realizada

- Ejecución **4**: análisis real de Gemini y ticket **#3**, con los tres archivos.
  Gemini identificó ACCESO-403 en el PDF; el TXT no se envió al modelo.
- Ejecución **5**: PDF deliberadamente inválido. Gemini rechazó la solicitud;
  el respaldo creó el ticket **#4 [REVISAR]** con los archivos originales.
- La conexión IMAP se había probado correctamente. Estas pruebas de adjuntos
  usan datos ficticios inyectados en la rama manual, no mensajes reales del buzón.

Pruebas locales:

```bash
node workflows/test-workflow.cjs
node workflows/test-attachments.cjs
```

## Límites de la demo

No envía respuestas por correo, no asigna técnicos ni actualiza conversaciones.
No tiene deduplicación persistente: cada ejecución exitosa crea un ticket.
IMAP usa `UNSEEN` y seguimiento de mensajes nuevos, sin marcar como leído.
Ante fallos revisar las ejecuciones guardadas; no asumir que IMAP volverá a emitir
el mensaje al reconectarse. Si el POST del ticket termina con timeout, buscar su
Message-ID en Redmine antes de repetirlo. El flujo conserva los originales en la
ruta de procesamiento; si faltan los propios datos binarios, no puede recuperarlos.

Los archivos de `nodes/` contienen los fragmentos nuevos de los nodos Code para
revisión y pruebas. n8n ejecuta el código embebido en el JSON, no lee esos archivos
desde el servidor: cualquier cambio debe actualizar también el workflow.

Referencias: [documentos en Gemini](https://ai.google.dev/gemini-api/docs/document-processing)
y [carga de archivos en Redmine](https://www.redmine.org/projects/redmine/wiki/rest_api#Attaching-files).
