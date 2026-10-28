# Despliegue del portal y la API

El servicio de clasificación está organizado en [nexpapi/](../../nexpapi/README.md),
con su aplicación, Dockerfile, dependencias y Compose. La lógica del modelo
se comparte con `python/src`; la categoría final la determina Python.

El portal Streamlit utiliza [compose.yaml](../compose.yaml),
`Dockerfile.streamlit` y `requirements-streamlit.txt` de esta carpeta.

Para operar la API, seguir las [instrucciones de NexpAPI](../../nexpapi/README.md).
La limpieza de firmas y datos sensibles se ejecuta localmente en n8n.
