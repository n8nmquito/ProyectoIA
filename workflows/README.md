# Correo → clasificador Python → OpenAI → Redmine

El flujo principal está activo en [n8n](http://185.208.207.203:5678/workflow/opxBwpGpRDrbQeHn).
El clasificador usa el archivo real modelo_clasificador_300.pkl (SVM calibrada),
servido por una API Python dentro de Docker. Ya no carga el modelo demo desde
PostgreSQL. OpenAI analiza el correo y consulta Redmine; Gemini está desconectado.

## Recorrido

Correo → normalizar → API Python → validar predicción → seleccionar adjuntos →
agente OpenAI → decidir relevancia → comparar categorías → preparar ticket →
validar proyecto/tipo/categoría → validar responsable → subir originales → crear
ticket → preparar confirmación.

Python recibe solo título y cuerpo y sirve para comparación. El agente mantiene
la decisión de categoría y propone prioridad y responsable. No hay aprobación
humana obligatoria antes de crear el ticket. La baja confianza Python no bloquea
por sí sola el alta. Coincidir con el agente no demuestra exactitud.

El agente devuelve tipo_ticket por nombre (Errores/Soporte). El código obtiene
su ID del catálogo habilitado en el proyecto. No se admite un ID inventado, ni
se fija el valor 2 ni se deduce por el orden de una lista. Se comprueban además
proyecto activo, categoría real, membresía y rol asignable con view_issues.

El agente puede recibir imágenes PNG/JPEG/WebP/PDF: hasta cuatro archivos,
4 MiB por archivo y 8 MiB en total. Todos los originales se conservan para
Redmine. La selección no anonimiza archivos ni garantiza su lectura.

## Importar y configurar

correo-ia-redmine.json y correo-ia-redmine-python300.json son exportaciones de la
misma versión, inactivas y sin credenciales. Hay que reasignarlas al importar.
No importar una copia sobre un flujo activo sin guardar antes su versión.
Ver [configuración](GUIA_CONFIGURACION.md), [proyecto Python](../python/README.md)
y [arquitectura completa](../python/docs/arquitectura.md).

La API interna usa http://clasificador-python:8000/predict con X-API-Key en una
credencial Header Auth de n8n. La clave permanece en .env del servicio y en la
credencial cifrada; no debe copiarse en documentos, exportaciones ni capturas.

## Pruebas verificadas

La prueba inicial de 24 correos creó 20 tickets y bloqueó cuatro propuestas de
tipo no habilitado. Tras resolver el tipo por nombre se repitieron esos cuatro:
4/4 crearon tickets DEMO en las ejecuciones 28517–28520, tickets 40–43. No se
repitieron los otros 20 ni se enviaron confirmaciones. Los resultados iniciales
y posteriores permanecen separados en python/results/n8n_produccion/.

```bash
node workflows/test-workflow.cjs
node workflows/test-assignment.cjs
node workflows/test-attachments.cjs
```

Las herramientas del agente son consultas GET. La creación de tickets y los
avisos posteriores sí tienen efectos reales. La rama Prueba manual → Correo de
ejemplo puede crear un ticket DEMO. Revisar si ya existe antes de repetir una
ejecución fallida para no duplicar solicitudes.

La privacidad y los límites del agente se documentan en
[consideraciones éticas](../python/docs/consideraciones_eticas.md).
