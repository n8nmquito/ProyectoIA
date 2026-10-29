# Notificaciones de cambios de estado

Flujo independiente: **Mquito | Avisos de cambios de estado Redmine**.

[Ver en n8n](http://185.208.207.203:5678/workflow/5Cga0y295UooA5nI)

## Recorrido

1. Cada un minuto consulta todos los tickets del proyecto Tickets de novedades (ID 1), incluidos cerrados, con paginación de 100.
2. Obtiene exclusivamente el campo personalizado **Correo del solicitante** (ID 1). No extrae destinatarios de la descripción, del autor ni de la IA.
3. Guarda la primera observación en PostgreSQL sin notificar. En consultas posteriores compara el ID de estado; cambios de asunto o responsable no disparan correos.
4. Registra cada transición con una revisión única por ticket. Sin dirección válida, registra `suppressed` y el motivo.
5. Reserva hasta 50 avisos pendientes por ejecución y los envía por Gmail. El mensaje incluye número, asunto, estado anterior, nuevo y enlace.
6. Registra `sent` cuando SMTP acepta un destinatario; ante error registra `failed`.

## Validación del correo

Admite una sola dirección con formato de correo, hasta 254 caracteres. Rechaza vacíos, listas de destinatarios, saltos de línea, direcciones de ejemplo, el propio buzón de integración y nombres automáticos conocidos. Esta comprobación no demuestra que exista el buzón ni garantiza la entrega. Una aceptación SMTP tampoco confirma lectura o llegada a la bandeja.

## PostgreSQL

Base `n8n`, esquema separado `ticket_notify`, usuario dedicado `mquito_ticket_notify`. No modifica las tablas de n8n ni de Redmine.

- `ticket_state`: último estado observado y revisión.
- `notifications`: transición, destinatario, estado de envío y fechas.

La función `observe(jsonb)` utiliza una transacción y bloqueo para evitar repetir una transición ante consultas simultáneas. Las respuestas antiguas de Redmine no sobrescriben estados más recientes. La reserva de avisos usa `FOR UPDATE SKIP LOCKED`.

Los estados son `pending`, `sending`, `sent`, `failed` y `suppressed`. Los fallos no se reenvían automáticamente. Si el proceso se interrumpe tras entregar a SMTP pero antes de guardar el resultado, el aviso puede quedar `sending`: comprobar Gmail/n8n antes de reintentarlo manualmente. Esto prioriza evitar duplicados, pero no garantiza entrega exactamente una vez. Si hay más de 50 pendientes, se procesan en siguientes consultas.

Corregir un correo no reenvía cambios antiguos suprimidos; se aplicará al siguiente cambio de estado. Los cambios intermedios que ocurran y se reviertan entre consultas pueden no detectarse: se compara el estado observado, no el historial completo.

## Configuración

La [exportación del flujo de avisos de 10 nodos](../../n8n/Mquito%20_%20Avisos%20de%20cambios%20de%20estado%20Redmine.json) está en `n8n/`. Conserva las referencias a las credenciales de origen. Para importarla, sigue la [guía de exportaciones](../../n8n/README.md). La plantilla `workflows/notificar-estados-redmine.json` se conserva por separado, desactivada y sin credenciales.

- Redmine: la credencial Header Auth existente, `X-Redmine-API-Key`.
- Gmail: la credencial SMTP existente, `smtp.gmail.com:465` con TLS.
- PostgreSQL: credencial dedicada de seguimiento; secreto en `.secrets/status-notifications-postgres.json`, excluido de Git.
- Frecuencia: nodo **Cada minuto**.
- Proyecto y campo: ID 1 en ambos casos; ajustar si se importa en otra instalación.

`notificar-estados-redmine.json` se exporta desactivado y sin credenciales. Para reinstalar, ejecutar desde la raíz `python workflows/status-notifications/setup-postgres.py` con psycopg disponible y `.env` configurado; importar el JSON y asignar las tres credenciales antes de publicar. El script usa `schema.sql` y conserva la contraseña local existente.

Pruebas locales: `node workflows/status-notifications/test.cjs`. Se verificaron en PostgreSQL las lecturas iniciales, transición única, rechazo de datos antiguos y supresión por correo inválido mediante una transacción revertida.
