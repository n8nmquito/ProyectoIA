# Correo → clasificador Python → OpenAI → Redmine

El flujo principal está activo en [n8n](http://185.208.207.203:5678/workflow/opxBwpGpRDrbQeHn).
El clasificador usa el archivo real modelo_clasificador_300.pkl (SVM calibrada),
servido por una API Python dentro de Docker. Ya no carga el modelo demo desde
PostgreSQL. OpenAI analiza el correo y consulta Redmine; Gemini está desconectado.

## Recorrido

Correo → normalizar → limpiar firma/datos en Python → validar texto limpio → API Python → validar predicción → seleccionar adjuntos →
agente OpenAI → decidir relevancia → aplicar categoría Python → preparar ticket →
validar proyecto/tipo/categoría → consultar categorías y miembros → resolver y validar responsable → subir originales → crear
ticket → preparar confirmación.

Python recibe título y cuerpo y determina la categoría final. El agente recibe
esa categoría y prepara resumen, descripción, relevancia, prioridad, tipo y
proyecto. El nodo Aplicar categoría Python impide sobrescribir la categoría.
Si la API falla o su respuesta no es válida, no se crea el ticket y se deriva
a revisión. La baja confianza o un desacuerdo del agente marcan revisión; no
cambian la categoría. El agente conoce la predicción: coincidir no constituye
una evaluación independiente ni demuestra exactitud.

El responsable configurado en la categoría real de Redmine tiene prioridad
sobre la propuesta del agente. Dos consultas GET recuperan categorías y miembros;
el código resuelve usuario, membresía y rol, y las consultas existentes validan
la membresía y el permiso asignable. Si el responsable configurado no puede
verificarse, se detiene el alta para revisión. Sin responsable configurado se
puede usar la propuesta del agente, siempre validada.

El agente devuelve tipo_ticket por nombre (Errores/Soporte). El código obtiene
su ID del catálogo habilitado en el proyecto. No se admite un ID inventado, ni
se fija el valor 2 ni se deduce por el orden de una lista. Se comprueban además
proyecto activo, categoría real, membresía y rol asignable con view_issues.

El agente puede recibir imágenes PNG/JPEG/WebP/PDF: hasta cuatro archivos,
4 MiB por archivo y 8 MiB en total. Todos los originales se conservan para
Redmine. La selección no anonimiza archivos ni garantiza su lectura.

## Importar y configurar

correo-ia-redmine.json y correo-ia-redmine-python300.json son exportaciones de la
misma versión, inactivas y sin credenciales. Hay que reasignarlas al importar.
No importar una copia sobre un flujo activo sin guardar antes su versión.
Ver [configuración](GUIA_CONFIGURACION.md), [proyecto Python](../python/README.md)
y [arquitectura completa](../python/docs/arquitectura.md).

La API interna usa http://nexpapi:8000/predict con X-API-Key en una
credencial Header Auth de n8n. La clave permanece en .env del servicio y en la
credencial cifrada; no debe copiarse en documentos, exportaciones ni capturas.

## Pruebas verificadas

La prueba inicial de 24 correos creó 20 tickets y bloqueó cuatro propuestas de
tipo no habilitado. Tras resolver el tipo por nombre se repitieron esos cuatro:
4/4 crearon tickets DEMO en las ejecuciones 28517–28520, tickets 40–43. No se
repitieron los otros 20 ni se enviaron confirmaciones. Los resultados iniciales
y posteriores permanecen separados en python/results/n8n_produccion/.

```bash
node workflows/test-workflow.cjs
node workflows/test-assignment.cjs
node workflows/test-attachments.cjs
```

Las herramientas del agente son consultas GET. La creación de tickets y los
avisos posteriores sí tienen efectos reales. La rama Prueba manual → Correo de
ejemplo puede crear un ticket DEMO. Revisar si ya existe antes de repetir una
ejecución fallida para no duplicar solicitudes.

La privacidad y los límites del agente se documentan en
[consideraciones éticas](../python/docs/consideraciones_eticas.md).

## Pruebas de categoría final

```bash
node workflows/test-python-category.cjs
```

Pruebas locales sin crear tickets: desacuerdo Otros/Aplicaciones, baja confianza,
API inválida, responsable configurado por categoría, rechazo de rol no asignable
y conexiones de la plantilla. El ticket histórico #49 conserva su categoría
anterior; la política nueva se aplica a las siguientes ejecuciones.

## Limpieza de texto antes del clasificador

El nodo de código **Limpiar firma y datos** ejecuta JavaScript dentro de n8n,
sin llamadas HTTP para limpiar el correo. Su código está en
`nodes/limpiar-correo.js`. Envía asunto/cuerpo limpios a `/predict` y al agente;
si no queda texto útil, deriva a revisión sin usar el original como respaldo.
**Unir correo y predicción** conserva el texto y los adjuntos junto con la
respuesta de la API. El selector de adjuntos valida esa respuesta antes del
agente; no existe un segundo nodo que vuelva a clasificar el correo.

Se quitan firmas habituales, bloques de firma HTML y avisos de confidencialidad.
Se redactan correos, teléfonos/números largos, IP, enlaces, credenciales y
campos personales etiquetados. Las reglas no garantizan reconocer todos los
nombres libres ni toda información sensible. Los adjuntos no se anonimizan.
El original sigue disponible para el ticket y en los registros de n8n; esta
limpieza no elimina los datos de esos almacenamientos.

El disparador IMAP usa UNSEEN y conserva `lastMessageUid`: mensajes antiguos
que sigan sin leer no se reprocesan automáticamente. Para comprobar el flujo
debe entrar un correo nuevo; reiniciar el cursor puede duplicar tickets.
