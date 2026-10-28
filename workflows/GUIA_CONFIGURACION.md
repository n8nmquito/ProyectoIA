# Configuración del flujo integrado

## Plantilla y servicios

Importar primero [revision-aviso-error.json](revision-aviso-error.json) y asignar su SMTP. Después usar [correo-ia-redmine-python300.json](correo-ia-redmine-python300.json), la plantilla vigente de 41 nodos, y seleccionar ese subflujo en **Revisión y aviso - Subflujo**. `correo-ia-redmine.json` es una referencia histórica con otra lógica de clasificación.

| Nodo o servicio | Configuración |
|---|---|
| Leer buzón IMAP | Credencial del buzón, host/puerto/TLS del proveedor, INBOX y formato Resolved |
| Limpiar firma y datos | Nodo Code JavaScript local; no requiere servicio ni credencial adicional |
| Consultar API - Modelo 300 | `POST http://nexpapi:8000/predict`; Header Auth con nombre `X-API-Key` |
| Agente OpenAI | Credencial del proveedor y modelo `gpt-4.1-mini` |
| Herramientas y nodos Redmine | Header Auth con nombre `X-Redmine-API-Key` |
| Avisos de correo | Credencial SMTP y remitente autorizado; el aviso de error se envía desde el subflujo |
| Revisión y aviso - Subflujo | Execute Sub-workflow, entrada `context` de tipo objeto, esperar finalización |

Las claves se administran en n8n y en los archivos privados del servicio. `X-API-Key` debe coincidir con `CLASSIFIER_API_KEY` del `.env` de NexpAPI. No escribir secretos en el flujo exportado ni en Git.

NexpAPI comparte la red Docker de n8n y no publica el puerto 8000. El host interno es `nexpapi`, no `localhost`. Consultar [NexpAPI](../nexpapi/README.md) y [operación del despliegue](../python/deploy/DESPLIEGUE_REALIZADO.md).

## Entrada, salida y errores

1. **Limpiar firma y datos** quita firmas y redacta datos sensibles del asunto/cuerpo dentro de n8n.
2. **Consultar API - Modelo 300** envía solo `titulo` y `cuerpo` limpios a `/predict`.
3. **Unir correo y predicción** reúne el correo limpio, sus adjuntos y la respuesta.
4. **Seleccionar adjuntos para IA** verifica que la respuesta corresponda a `modelo_clasificador_300`, con 300 muestras, categoría y probabilidades válidas; luego prepara archivos para el agente.
5. El agente recibe la categoría Python y analiza el correo. **Aplicar categoría Python** vuelve a fijarla antes de preparar el ticket.

Si falla la limpieza, la API o la validación de la respuesta, la ejecución invoca **Revisión y aviso - Subflujo**, que registra el caso y evalúa si corresponde avisar al remitente. No pasa al agente ni crea un ticket con una categoría de respaldo. Los originales siguen disponibles para Redmine; los adjuntos no se anonimizan.

## Tipo, categoría y responsable

El agente devuelve `tipo_ticket` como **Errores** o **Soporte**. El código consulta los tipos habilitados y obtiene un ID único. Un nombre ausente, ambiguo o no habilitado impide crear el ticket.

Configurar las categorías **Accesos, Aplicaciones, Infraestructura y Otros** con nombres únicos por proyecto. Si una tiene responsable predeterminado, el código lo prioriza y verifica su membresía, rol asignable y permiso `view_issues`. Si esa verificación falla, se detiene el alta para revisión.

Sin responsable configurado, se valida la propuesta del agente. El flujo puede dejar el ticket sin asignar y marcado para revisión si no hay una propuesta válida. Las consultas actuales recuperan hasta 100 miembros: proyectos mayores requieren ampliar la paginación.

## Comprobación antes de publicar

- Importar el subflujo antes del principal y reasignar las credenciales. Ambas plantillas se exportan desactivadas.
- Seleccionar **Mquito | Revisión y aviso de error** en el nodo de llamada y conservar **Wait For Sub-Workflow Completion** activado. El subflujo admite llamadas del mismo propietario.
- Comprobar que el nodo de limpieza sea Code JavaScript y que la API use `http://nexpapi:8000/predict`.
- Revisar las conexiones de error hacia **Revisión y aviso - Subflujo** y la presencia de **Aplicar categoría Python**.
- Ejecutar las pruebas locales indicadas en el [README](README.md#pruebas-y-diagnóstico).
- Para una prueba completa, preparar una copia aislada que sustituya creación de tickets y SMTP por comprobaciones. La rama manual del flujo principal sí puede generar un ticket real.

## Diagnóstico de una ejecución

Abrir **Executions** y revisar los nodos de limpieza, API y validación. Un estado `success` no demuestra que exista un ticket: comprobar **Resultado del ticket** y su ID en Redmine antes de reintentar.

La señal de revisión no obliga a una aprobación humana. Las validaciones comprueban formatos y catálogos, no la veracidad completa del resumen. OpenAI puede recibir texto limpio, adjuntos seleccionados y respuestas de herramientas; la limpieza no equivale a anonimización completa.


## Datos que recibe el subflujo

La entrada es `context` de tipo objeto. Para probar desde otro flujo, usar datos ficticios y `demo: true`:

```json
{
  "context": {
    "email": {
      "remitente": "demo@example.invalid",
      "asunto": "Prueba de revisión",
      "message_id": "demo-1",
      "demo": true
    },
    "raw": {"headers": {}},
    "origen": {"workflow_id": "flujo-origen", "execution_id": "ejecucion-origen"}
  }
}
```

Si se usa el remitente del correo sin normalizar, incluir `raw.from` y `raw.subject`. Para conservar el filtro de mensajes automáticos, pasar las cabeceras `auto-submitted`, `precedence` y `list-id` cuando existan. El subflujo no consulta nodos de su llamador: trabaja únicamente con esta entrada y conserva la referencia a la ejecución de origen.
