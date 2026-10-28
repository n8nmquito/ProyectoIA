# NexpAPI

API interna FastAPI que ejecuta el modelo Python de 300 correos y devuelve la
categoría final, confianza y probabilidades. La lógica compartida permanece en
`../python/src/api.py`; `app.py` es la entrada del servicio. La limpieza del
correo se realiza en un nodo de código de n8n, antes de llamar a la API.

## Instalación y arranque

Desde la raíz del repositorio, con el modelo de 300 correos ya entrenado:

```bash
cp nexpapi/.env.example nexpapi/.env
```

Configurar una clave aleatoria de al menos 32 caracteres en `CLASSIFIER_API_KEY`
y la misma clave en la credencial Header Auth de n8n (`X-API-Key`).
Con la red del proyecto principal ya creada:

```bash
docker compose --project-directory nexpapi -f nexpapi/compose.yaml up -d --build
docker compose --project-directory nexpapi -f nexpapi/compose.yaml ps
docker compose --project-directory nexpapi -f nexpapi/compose.yaml logs --tail=50
```

El contexto de construcción es la raíz del repositorio. Por defecto copia
`python/models/modelo_clasificador_300.pkl` y `python/config.yaml`. Para conservar
un modelo desplegado por separado, `NEXPAPI_MODEL_DIR` permite indicar otra
carpeta dentro del repositorio; en producción se utiliza `nexpapi/models`.
Solo la copia de `nexpapi/models/` y el `.env` del despliegue quedan fuera de Git. Los modelos de entrega están versionados en [python/models/](../python/models/README.md).

## Integración y producción

- Directorio: `/mquito/mquito-ticket/nexpapi`.
- Contenedor y servicio: `nexpapi`.
- Proyecto Compose: `mquito-nexpapi`.
- Red externa: `correo-tickets_automatizacion`.
- URL interna: `http://nexpapi:8000/predict`.
- Salud: `GET /health`; la API no publica el puerto 8000 en Internet.
- Entrada: JSON con `titulo` y `cuerpo`; autenticación `X-API-Key`.
- No reentrena modelos, no limpia firmas y no llama a OpenAI.

Ejemplo de entrada:

```json
{"titulo":"Error JDE", "cuerpo":"No guarda la orden de compra."}
```

La respuesta incluye `categoria`, `confianza`, `probabilidades`,
`requiere_revision`, `modelo_version` y `muestras_entrenamiento`.
La política `unless-stopped` reinicia el contenedor tras una caída o reinicio
del servidor, salvo que se haya detenido manualmente.
