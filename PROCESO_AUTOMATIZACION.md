# Proceso de automatización entregado

La arquitectura completa, parámetros y límites están en
[python/docs/arquitectura.md](python/docs/arquitectura.md).
La privacidad del sistema completo está en
[python/docs/consideraciones_eticas.md](python/docs/consideraciones_eticas.md).

## Recorrido actual

1. n8n recoge el correo IMAP, normaliza texto y conserva los adjuntos originales.
2. Consulta la API Python privada con título y cuerpo. Se usa el modelo de 300
   correos; la respuesta aporta categoría y probabilidades para comparar.
3. Selecciona imágenes/PDF dentro de los límites configurados y pasa el correo
   al agente OpenAI. Gemini no participa en la versión probada.
4. El agente decide relevancia, resume, clasifica y consulta catálogos reales
   de Redmine. La categoría Python no fuerza su decisión.
5. Si corresponde crear ticket, se comparan las categorías y se prepara la
   propuesta. El agente devuelve tipo_ticket por nombre: Errores o Soporte.
6. El código consulta los tipos habilitados, obtiene el ID real y valida
   proyecto y categoría. Un tipo ausente o ambiguo impide crear el ticket.
7. Comprueba usuario, membresía y rol asignable antes de asignar responsable.
8. Recupera y sube todos los archivos originales a Redmine y crea el ticket.
9. Prepara el aviso al remitente. Las pruebas DEMO no envían confirmaciones.

No se conceden permisos reales ni se resuelven incidentes automáticamente.
Sí se crean y asignan tickets después de validaciones, sin aprobación humana
obligatoria. La baja confianza Python no bloquea por sí sola el alta.

## Pruebas y límites

La prueba inicial de 24 correos creó 20 tickets y bloqueó cuatro tipos no
habilitados. Tras eliminar los IDs propuestos por el agente y resolver el tipo
por nombre, se repitieron los cuatro afectados: ejecuciones 28517–28520,
tickets DEMO 40–43, sin confirmaciones. No se repitió todo el lote.

Un estado success de n8n puede contener un rechazo por una salida de error
controlada. Verificar el ID final de Redmine antes de considerar completada la
solicitud o reintentar; no hay una garantía general de deduplicación.

Los resultados están en python/results/n8n_produccion/. Las métricas 280/20 del
clasificador no corresponden a una prueba independiente del modelo final de 300.
La revisión de etiquetas de los mismos 25 conocidos sigue pendiente y no puede
presentarse como evidencia de generalización a entradas nuevas.

OpenAI puede recibir texto, adjuntos seleccionados y respuestas de herramientas.
La limpieza de Python no anonimiza esas entradas. No hay auditoría de privacidad
ni cumplimiento normativo demostrado del sistema completo. El corpus inicial
no se publica porque su autorización no está confirmada.
