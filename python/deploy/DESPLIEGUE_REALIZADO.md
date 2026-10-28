# Despliegue actual de NexpAPI y Streamlit

## Estado vigente

| Componente | Configuración actual |
|---|---|
| API | Contenedor `nexpapi`, proyecto Compose `mquito-nexpapi` |
| Directorio de API | `/mquito/mquito-ticket/nexpapi` |
| Red compartida | `correo-tickets_automatizacion` |
| URL desde n8n | `http://nexpapi:8000/predict` |
| Modelo de la API | 300 correos; SHA-256 `2905ce4167d90281106ff7a37f6211114eccf459c1764d8ac5c61f0b81bf6a87` |
| Portal | `mquito-portal-streamlit-1`, proyecto `mquito-portal`, puerto 8501 |
| Flujo principal n8n | `opxBwpGpRDrbQeHn`, 41 nodos y categoría final Python |

NexpAPI exige `X-API-Key` y no publica el puerto 8000. Su `.env` permanece privado. La API reutiliza `python/src` y `python/config.yaml`; el modelo desplegado está en `nexpapi/models` mediante `NEXPAPI_MODEL_DIR`.

El portal usa sus modelos de `python/models` en solo lectura y conserva el historial en un volumen SQLite. Los datos y los modelos entregados están disponibles en el repositorio; las claves y las copias privadas del despliegue se mantienen aparte. Consultar [NexpAPI](../../nexpapi/README.md), [modelos](../models/README.md) y [configuración de n8n](../../workflows/GUIA_CONFIGURACION.md).

## Operación

Para consultar o reconstruir únicamente NexpAPI:

```bash
cd /mquito/mquito-ticket/nexpapi
docker compose -p mquito-nexpapi ps
docker compose -p mquito-nexpapi logs --tail=50
docker compose -p mquito-nexpapi up -d --build
```

Para el portal:

```bash
cd /mquito/mquito-ticket/python
docker compose -p mquito-portal ps
docker compose -p mquito-portal logs --tail=50 streamlit
docker compose -p mquito-portal up -d --build --wait streamlit
```

Ambos servicios utilizan `unless-stopped`. Los volúmenes conservan historial y datos entre recreaciones. Las credenciales, modelos y configuración deben respaldarse antes de actualizar.

## Comportamiento del flujo actual

La limpieza de firmas y datos sensibles se ejecuta en un nodo Code JavaScript de n8n. NexpAPI recibe título/cuerpo limpios y determina la categoría. Si la limpieza, la API o su respuesta fallan, se deriva a revisión antes de ejecutar el agente.

OpenAI prepara el análisis y propone prioridad, tipo y proyecto. El código fija la categoría Python, consulta el responsable y valida los catálogos, la membresía y el rol. Los originales y adjuntos se conservan para Redmine; los adjuntos no se anonimizan.

La plantilla vigente es [correo-ia-redmine-python300.json](../../workflows/correo-ia-redmine-python300.json). La otra exportación es histórica y no sirve como sustituto de la configuración actual.

## Evidencia actual

- La ejecución aislada n8n **28845** verificó dos correos ficticios, limpieza local, NexpAPI y adjuntos, sin crear tickets ni enviar correos. El diagnóstico se archivó y el flujo principal quedó activo.
- La evaluación de los modelos reentrenados del portal está en [results/produccion](../results/produccion/metrics/version_evaluation.json). La interfaz muestra métricas solo si el hash coincide con el archivo seleccionado.
- El reporte de [pruebas Python](../results/metrics/pytest.xml) registra **96 pruebas aprobadas**. Las suites JavaScript y sus alcances están descritos en el [README del flujo](../../workflows/README.md#pruebas-y-diagnóstico).

## Reversión de una actualización

1. Antes del cambio, guardar la versión publicada de n8n, el commit y la imagen en uso, la configuración y los hashes de los modelos. Conservar los volúmenes y archivos privados.
2. Elegir una versión previamente verificada que mantenga la limpieza local, la categoría final Python y el endpoint `nexpapi:8000`. Revisar su compatibilidad con el código y modelo que se va a restaurar.
3. Probar la versión en una copia aislada, con la creación Redmine y SMTP sustituidas por comprobaciones, antes de publicarla.
4. Si se restaura código de un servicio, reconstruir solo ese servicio con los comandos anteriores. Comprobar salud, una predicción y su hash; para el portal, verificar también la lectura de métricas y el historial.
5. Confirmar en n8n que el flujo está activo y que las rutas de error y la validación de categoría siguen presentes. Revisar si existe un ticket antes de reintentar ejecuciones fallidas.

El historial de n8n también contiene versiones anteriores a la integración actual. Su antigüedad no las convierte en una reversión compatible: algunas usan el modelo PostgreSQL o dejan la categoría al agente. La reversión debe conservar las reglas vigentes del sistema.

## Evidencia histórica

Estos registros describen etapas anteriores y se conservan para trazabilidad:

| Etapa | Evidencia registrada |
|---|---|
| Integración inicial de API | Ejecuciones **28474** y **28475**: paridad, adjuntos y recuperación ante fallo de API |
| Corrección del tipo de ticket | Ejecuciones **28517–28520**, tickets DEMO **40–43**: resolución de Errores/Soporte por nombre |
| Renombrado a NexpAPI | Contenedor anterior retirado; archivos auxiliares conservados en `backups/nexpapi-layout-20261028` |

Los respaldos iniciales de API y flujo están en `/mquito/mquito-ticket/backups/classifier300`; son archivos privados del servidor, no componentes necesarios para una instalación nueva. El mecanismo antiguo de PostgreSQL queda como referencia histórica, no como instrucción operativa actual.
