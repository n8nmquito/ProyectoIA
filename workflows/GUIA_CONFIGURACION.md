# Configuración del flujo integrado

## Servicios y credenciales

| Nodo o servicio | Configuración |
|---|---|
| Leer buzón IMAP | Credencial del buzón, host/puerto/TLS según proveedor, INBOX y formato Resolved |
| Consultar API - Modelo 300 | POST http://clasificador-python:8000/predict; Header Auth con Name X-API-Key |
| OpenAI - Cargar API key | Credencial OpenAI del agente, sin escribirla en código |
| Nodos HTTP y herramientas Redmine | Header Auth con Name X-Redmine-API-Key y clave real de Redmine |
| Avisos de correo | Credencial SMTP y remitente autorizado |

Las credenciales IMAP/SMTP/OpenAI/Redmine se administran en n8n. La clave de la
API Python debe coincidir con CLASSIFIER_API_KEY del .env del servicio. No usar
la contraseña SSH como clave de API ni publicar secretos en Git.

La URL del servicio Python se resuelve dentro de la red Docker compartida;
localhost de la PC no sirve desde el contenedor n8n. La API no necesita publicar
un puerto a Internet. En otro servidor debe adaptarse la red y el nombre del
servicio. Ver python/deploy/DESPLIEGUE_REALIZADO.md para operación y reversión.

## Entrada y salida de Python

El cuerpo JSON del nodo HTTP contiene solo titulo y cuerpo del correo
normalizado. La respuesta debe identificar modelo_clasificador_300 y 300 muestras,
además de categoría, confianza y probabilidades. El adaptador comprueba esos
campos y recupera los adjuntos originales. Si la API falla, marca clasificación
no disponible y continúa el agente; no inventa una categoría de respaldo.

## Tipo, categoría y responsable

El esquema del agente requiere tipo_ticket con Errores o Soporte. El agente no
devuelve tracker_id. El nodo Validar proyecto y tipo consulta los tipos
habilitados del proyecto y resuelve el nombre a un ID único. Si el nombre falta,
es ambiguo o no está habilitado, detiene la creación; no se fuerza otro tipo.

Redmine debe tener las categorías Accesos, Aplicaciones, Infraestructura y Otros
con nombres únicos por proyecto. Puede configurarse responsable predeterminado
por categoría. El código valida usuario, membresía y rol antes de asignarlo;
no aplica una asignación que no pueda comprobar.

## Prueba y diagnóstico

Abrir el flujo principal y su pestaña Executions. La rama manual usa un correo
ficticio DEMO, pero puede crear un ticket real. Las pruebas controladas mantienen
remitente de ejemplo y no envían confirmaciones. No introducir credenciales en
el cuerpo del correo ni adjuntos sensibles.

Un estado success en n8n puede incluir un rechazo controlado por validación.
Comprobar Resultado del ticket y su ID en Redmine. Si no existe, revisar las
salidas de error de proyecto, tipo, categoría y asignación antes de reintentar.
No repetir ciegamente el alta porque podría existir un ticket ya creado.

La señal de revisión Python no obliga a una revisión humana. Los controles
formales no demuestran que el resumen generado sea verdadero. Texto y adjuntos
seleccionados, junto con respuestas de herramientas, pueden enviarse a OpenAI.
