# Flujos exportados de n8n

Estos archivos son las copias exportadas de los dos flujos del sistema.

| Archivo | Qué hace | Nodos |
|---|---|---:|
| [Mquito — Correo → IA → Ticket Redmine](Mquito%20_%20Correo%20%E2%86%92%20IA%20%E2%86%92%20Ticket%20Redmine.json) | Recibe correos, consulta el clasificador Python y OpenAI, valida los datos y crea el ticket con sus adjuntos en Redmine | 41 |
| [Mquito — Avisos de cambios de estado Redmine](Mquito%20_%20Avisos%20de%20cambios%20de%20estado%20Redmine.json) | Revisa los estados de los tickets y envía un correo al solicitante cuando detecta un cambio | 10 |

## Cómo usarlos

1. Descarga el JSON del flujo que necesites.
2. En n8n, abre el menú del editor y elige **Import from File**.
3. Revisa las credenciales, las direcciones de los servicios, el proyecto y el correo del remitente. Las referencias a credenciales del servidor original no crean esas credenciales en otra instalación.
4. Comprueba el flujo antes de publicarlo: puede crear tickets y enviar correos reales.

Los archivos conservan el campo `active: true` de la exportación. Guardarlos en Git no ejecuta ni publica los flujos en n8n. No contienen datos de prueba fijados en `pinData`.

## Diferencia con las plantillas

En [`workflows/`](../workflows/README.md) se conservan las plantillas desactivadas y sin referencias a credenciales para preparar otra instalación. Estos archivos de `n8n/` conservan los nombres y las referencias de la instalación de origen. No se han reemplazado las plantillas ni sus pruebas.

Consulta la [guía de configuración](../workflows/GUIA_CONFIGURACION.md), el [recorrido completo con imágenes](../README.md#uso-del-flujo-completo-de-correo-a-redmine) y el [seguimiento de estados](../workflows/status-notifications/README.md).
