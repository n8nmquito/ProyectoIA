# Clasificador Python integrado con n8n

Servicio: ticket-clasificador-clasificador-1
Directorio: /mquito/mquito-ticket/clasificador-python
Red Docker externa: correo-tickets_automatizacion
URL desde n8n: http://clasificador-python:8000/predict
No tiene puerto publicado en Internet.
Modelo: models/modelo_clasificador_300.pkl, SVM calibrada, 300 correos.
La clave está en .env (permisos 600) y en la credencial cifrada de n8n Clasificador Python 300 - API interna. No incluirla en documentación ni en Git.

## Operación

Desde este directorio:

docker compose -p ticket-clasificador -f compose.yaml ps
docker compose -p ticket-clasificador -f compose.yaml logs --tail=50
docker compose -p ticket-clasificador -f compose.yaml up -d --build

La política unless-stopped reinicia el servicio con Docker después de reiniciar el servidor, salvo que se haya detenido manualmente. No ejecutar docker compose down en el proyecto principal para administrar este servicio.

## n8n

Flujo activo: opxBwpGpRDrbQeHn
Versión publicada: 81c22841-3088-4d79-bfdf-798073d75775
Se reemplazaron Cargar modelo ML - PostgreSQL y Clasificar correo - TF-IDF por Consultar API - Modelo 300 y Clasificar correo - Modelo 300.
Se conservan credenciales, agente, adjuntos y validaciones de Redmine.
Python sigue como comparación; el agente conserva la decisión final.

La API requiere X-API-Key y recibe solo titulo/cuerpo. No se enviaron datos de entrenamiento al servidor: solo código y modelo. Los 25 casos de prueba sintéticos se guardaron en la carpeta privada de backups para verificar paridad.
El agente externo posterior mantiene sus entradas anteriores: esta integración no anonimiza ni limita lo que recibe ese agente.

## Evidencia

Backups y resultados: /mquito/mquito-ticket/backups/classifier300
- workflow-opxBwpGpRDrbQeHn-before.json: borrador original.
- workflow-published-before.json: versión publicada original.
- workflow-published-after.json: versión integrada.
- api-test-results.json: 25 predicciones idénticas a Python, autenticación 401 y validación 422.
- n8n-test-results.json: ejecución aislada 28474 con conservación del adjunto.
- n8n-failure-test-results.json: ejecución aislada 28475 con API inaccesible y recuperación correcta.
No se ejecutaron nodos de agente, Redmine ni notificaciones en estas pruebas.

## Reversión

En el historial de versiones de n8n, publicar de nuevo la versión f204482e-dcdd-4259-9398-f7c4cc9f8332, previa a la integración. La credencial PostgreSQL anterior se conserva. Verificar que vuelve la ruta Normalizar correo → Cargar modelo ML - PostgreSQL → Clasificar correo - TF-IDF.
Después de restaurar el flujo, puede detenerse solo esta API con:

docker compose -p ticket-clasificador -f compose.yaml stop

No eliminar las copias de seguridad ni detener el PostgreSQL del proyecto.

## Corrección de tipos y evidencia posterior

El agente devuelve tipo_ticket por nombre (Errores/Soporte) y el código resuelve
el ID desde los tipos habilitados del proyecto. La versión previa a esta corrección
está en workflow-before-tracker-fix.json y la corregida en workflow-after-tracker-fix.json,
dentro de la carpeta privada de backups. La reversión histórica de la integración
indicada arriba es más antigua; para revertir solo este cambio se debe usar la
versión anterior a la corrección en el historial de n8n.

Regresión de casos 5/6/13/22: ejecuciones 28517–28520, tickets DEMO 40–43,
4/4 correctos sin confirmaciones. No se modificaron modelos ni se reinició la API.
La nueva documentación está en python/docs y las pruebas S5 se ejecutan localmente.
