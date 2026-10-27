# Conectar el modelo de 300 correos con n8n

Estado: API desplegada en /mquito/mquito-ticket/clasificador-python y flujo activo actualizado el 26/10/2026. Ver DESPLIEGUE_REALIZADO.md para evidencia, operación y reversión. Las instrucciones siguientes sirven para reproducir la instalación.

## Qué cambia

Normalizar correo → Consultar API - Modelo 300 → Clasificar correo - Modelo 300 → Seleccionar adjuntos para IA → Agente → comparación → validaciones → Redmine.

La API ejecuta el archivo real models/modelo_clasificador_300.pkl (SVM calibrada), con la misma limpieza y probabilidades que Python. No reentrena. Se elimina de esta copia la consulta del modelo demo en PostgreSQL. Los cuatro modelos y los datasets se conservan.

La categoría Python continúa como comparación: el agente mantiene la decisión que tenía en el flujo original. Convertir Python en decisor final requiere otra modificación explícita. Coincidir con el agente no demuestra exactitud.

Solo se envían titulo y cuerpo a esta API. Los adjuntos permanecen en n8n y se recuperan para Redmine. Esto no cambia lo que el agente externo recibe en los nodos posteriores. Esta API no llama a OpenAI ni Gemini.

## Prueba en Windows

Desde F:\Maria\python:

```powershell
python -m pip install -r deploy/requirements.txt
$env:CLASSIFIER_API_KEY = (python -c "import secrets; print(secrets.token_urlsafe(32))")
python -m uvicorn src.api:app --host 127.0.0.1 --port 8000 --no-access-log
```

En otra consola puede comprobarse http://127.0.0.1:8000/health y abrir /docs.
Para /predict, autorizar mediante el encabezado X-API-Key (en /docs añadirlo como parámetro).
No compartir la clave ni escribirla en el workflow. Conservarla en el gestor de credenciales.

IMPORTANTE: localhost de Windows no es localhost del servidor n8n. Este comando solo prueba la API en la PC. El servidor remoto no podrá llamarla con esa dirección.

Ejemplo de cuerpo POST /predict:

```json
{"titulo":"No puedo iniciar sesión", "cuerpo":"Mi cuenta quedó bloqueada al entrar al sistema"}
```

La respuesta incluye categoria, confianza (0–1), confianza_pct, probabilidades por clase, requiere_revision y muestras_entrenamiento=300. El umbral de revisión es 0.60, igual al valor actual del proyecto. Las probabilidades no garantizan acierto. HTTP 401 indica clave inválida; HTTP 422 indica entrada inválida. No se devuelve el texto del correo en los errores de validación ni se registra intencionalmente el contenido de las solicitudes.

## Dónde subir Python

El acceso al panel n8n no instala servicios en el sistema operativo. Hay dos opciones:

1. El administrador despliega esta API en Docker junto a n8n. Debe incorporar un servicio con build context en la raíz del proyecto y dockerfile deploy/Dockerfile, configurar CLASSIFIER_API_KEY y conectarlo a la red de n8n. La URL interna sería http://clasificador:8000/predict si ese es su nombre de servicio. No hace falta publicar el puerto hacia Internet.
2. Alojar el contenedor en un servicio externo con HTTPS. Obtener una URL estable accesible desde n8n. Revisar costes y tratamiento de datos antes de enviar correos reales.

El Dockerfile usa Python 3.10 y las versiones del entrenamiento; copia solo src y el modelo de 300, no los correos de entrenamiento. Se construye desde la raíz:

```bash
docker build -f deploy/Dockerfile -t clasificador-ti .
```

La clave se entrega como variable de entorno al crear el contenedor. El comando de arranque ya está en el Dockerfile, escucha en el puerto 8000. No incluir claves en la imagen. El proveedor o administrador debe configurar HTTPS si es accesible por Internet. No montar el socket Docker en n8n ni ejecutar instalaciones del servidor desde nodos del flujo.

## Configurar la copia del flujo

Archivo: F:\Maria\workflows\correo-ia-redmine-python300.json.

1. Importar como flujo NUEVO. La copia está inactiva y sin credenciales asignadas.
2. En Consultar API - Modelo 300 comprobar la URL exportada `http://clasificador-python:8000/predict`. Solo funciona si el servicio está desplegado y comparte la red Docker de n8n. Adaptar host y red si la instalación es diferente.
3. Crear una credencial Header Auth con Name X-API-Key y Value igual a CLASSIFIER_API_KEY. Seleccionarla en ese nodo.
4. Reasignar las credenciales habituales IMAP, Gemini/OpenAI, Redmine y correo saliente. El proveedor del agente se conserva tal como aparece en la copia local, que puede diferir de la versión activa del servidor.
5. Verificar la salida: modelo_version=modelo_clasificador_300 y muestras_entrenamiento=300. Comprobar probabilidades y que los adjuntos originales sobreviven al adaptador.
6. Si la API falla o responde con otro modelo, el adaptador marca clasificacion_no_disponible y conserva el correo; continúa el agente existente. No inventa una predicción de respaldo.
7. Probar primero hasta los nodos de clasificación. Ejecutar la rama manual completa también llama al agente y crea un ticket real en Redmine. Activar únicamente después de comprobar esta configuración y las credenciales.

El JSON actualizado corresponde al flujo integrado del servidor; se exporta inactivo y sin credenciales para importaciones seguras. El flujo existente en el servidor sí quedó publicado y activo.

## Pruebas

```powershell
python -m pip install pytest==8.3.4 httpx==0.28.1
python -m pytest tests/test_api.py -q
```

Se comprueba autenticación, validación sin devolver datos privados, rechazo de otro modelo y coincidencia exacta entre API y Python para los 25 correos. Esto comprueba la integración local, no mide precisión sin etiquetas humanas ni valida conectividad del despliegue remoto.
