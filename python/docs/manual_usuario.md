# Manual de usuario

Este manual cubre las pruebas del clasificador Python y el recorrido de una solicitud de soporte por correo hasta su seguimiento en Redmine. Para probar modelos, sigue los apartados 1 a 5; para enviar y consultar una solicitud, ve al [apartado 7](#7-enviar-una-solicitud-y-seguir-el-ticket). El [apartado 8](#8-direcciones-de-acceso-y-red-interna) explica las direcciones del navegador y las conexiones internas que aparecen en las capturas.

## 1. Guía paso a paso para usar la interfaz

1. Abre el [portal del clasificador](http://185.208.207.203:8501). Para ejecutarlo en tu computadora, sigue [Instalación y uso](../README.md#7-instalación-y-uso) y abre `http://localhost:8501`.
2. Elige **ES / EN** y el tema **Oscuro / Claro**, arriba a la derecha. El idioma cambia la pantalla; el modelo está entrenado con correos en español.
3. Entra en **Clasificar** y selecciona un modelo disponible. Se propone el de 300 correos si existe; las otras versiones permiten comparar resultados.
4. Escribe el **Título** y la **Descripción**, o pulsa **Prueba con ejemplo** para cargar un correo ficticio. Cada pulsación carga otro de los cuatro ejemplos.
5. Comprueba los datos: ambos campos deben tener letras. El formulario admite hasta **255 caracteres en el título y 16.000 en la descripción**. Para las pruebas, usa textos sin contraseñas ni información personal.
6. Pulsa **Clasificar** y espera el indicador de procesamiento. Si aparece un error, corrige lo indicado y vuelve a intentarlo.
7. En **Resultado**, revisa la categoría, la confianza y las probabilidades de las cuatro clases. Si hay un aviso de revisión, comprueba el correo manualmente. Una confianza alta tampoco garantiza un acierto.
8. Descarga la predicción en **Excel o CSV** con los botones situados debajo del gráfico.
9. Abre **Historial y comparación** para consultar las predicciones, descargarlas o seleccionar al menos dos para compararlas. Para comparar modelos, clasifica el mismo correo con otra versión.

El portal prueba el clasificador: **no crea tickets en Redmine ni ejecuta el flujo de correo de n8n**. Cambiar el modelo tampoco lo reentrena. Las capturas siguientes usan ejemplos ficticios; las cifras y los modelos disponibles pueden cambiar tras un nuevo entrenamiento.

## 2. Capturas de pantalla anotadas

Las marcas numeradas señalan los controles y sus funciones. Debajo de cada captura se explica cada número; las imágenes originales se conservan.

### Clasificar y leer el resultado

![Captura anotada: ejemplo, modelo, entrada, clasificación, confianza, probabilidades y descarga](../documentacion/imagenes/app/manual/01_clasificar.svg)

Usa las referencias **1–4** para cargar y clasificar el correo, y **5–7** para interpretar y descargar el resultado. Desplázate hacia abajo si algún botón queda fuera de la pantalla.

### Consultar Acerca de

![Captura anotada: preferencias, pestaña Acerca de, archivo, variables y datos del modelo](../documentacion/imagenes/app/manual/02_acerca.svg)

Aquí puedes identificar el modelo y revisar sus entradas. Más abajo aparecen parámetros, métricas disponibles y limitaciones. Los modelos reentrenados del portal ya tienen su reporte por hash; para el de 10 se explica por qué no hay CV viable. Si se cambia un archivo sin reevaluarlo, se informa en pantalla.

### Revisar el historial

![Captura anotada: pestaña Historial, enlace privado, registros y descargas](../documentacion/imagenes/app/manual/03_historial.svg)

La tabla muestra título, modelo, categoría, confianza y revisión. Conserva tu enlace para recuperar el historial y no lo compartas si contiene datos privados.

### Comparar predicciones

![Captura anotada: selección de registros, comparación de probabilidades y borrado del historial](../documentacion/imagenes/app/manual/04_comparar.svg)

Selecciona al menos dos registros. Los colores distinguen las predicciones; una barra más alta no demuestra que un modelo sea más preciso. **Borrar historial** elimina los registros de ese historial.

### Corregir una entrada inválida

![Captura anotada: campos obligatorios, botón Clasificar y mensaje de validación](../documentacion/imagenes/app/manual/05_validacion.svg)

El mensaje explica qué campo debes corregir. En este ejemplo el título está vacío: no se ejecuta la predicción hasta introducir un texto válido.

## 3. Explicación de cada funcionalidad

| Función | Cómo se utiliza |
|---|---|
| Idioma y tema | Los controles superiores cambian entre español/inglés y claro/oscuro |
| Selector de modelo | Muestra los archivos activos `modelo_clasificador_<cantidad>.pkl` de `models/`; no busca en carpetas de respaldo |
| Prueba con ejemplo | Carga título y descripción de un correo ficticio; vuelve a pulsar para probar otro |
| Formulario y validación | Introduce título y descripción; los mensajes indican campos vacíos, inválidos o demasiado largos |
| Clasificar | Ejecuta una predicción y muestra el estado de procesamiento o un mensaje de error |
| Resultado | Presenta una de las cuatro categorías, confianza, probabilidades y avisos de revisión |
| Gráfico interactivo | Compara las cuatro probabilidades; al pasar el cursor puedes consultar sus valores |
| Descargas | Guarda la predicción o el historial en CSV o Excel, con textos, modelo, probabilidades y datos de revisión |
| Acerca de | Explica el modelo, sus parámetros, métricas disponibles, limitaciones y advertencias |
| Historial | Conserva hasta 50 predicciones con la configuración actual. En el portal Docker persiste en el servidor; sin almacenamiento configurado, la ejecución local usa memoria de sesión |
| Comparación | Selecciona dos o más registros para comparar sus probabilidades. Usa el mismo correo si quieres comparar modelos |
| Borrar historial | Elimina las predicciones del historial actual; no borra los modelos ni archivos ya descargados |

La categoría es la de mayor probabilidad. El umbral actual de revisión es **60 %**; también se avisa cuando el texto no contiene vocabulario conocido. Son señales para revisar, no una comprobación de que la respuesta sea correcta.

## 4. Troubleshooting (problemas comunes y soluciones)

| Problema | Qué hacer |
|---|---|
| El portal no abre | Comprueba la conexión y la dirección. Si el problema continúa, informa a soporte; el servicio puede estar detenido |
| No aparecen modelos | Pide al responsable que compruebe `models/`. Los `.pkl` ya están incluidos en Git: actualiza el repositorio o consulta la guía de modelos. Recarga después de añadirlos |
| Se muestra un error al cargar el modelo | Comunica el nombre del archivo a soporte. No descargues modelos de una fuente desconocida ni cambies su nombre para forzar la carga |
| El formulario rechaza el correo | Completa ambos campos con letras y respeta los límites de 255 y 16.000 caracteres |
| La confianza es baja o la categoría parece incorrecta | Revisa el caso completo. Prueba una descripción más clara sin inventar datos; no uses la predicción como decisión definitiva |
| No aparecen métricas en Acerca de | El modelo puede haberse reentrenado sin actualizar su evaluación. La clasificación puede funcionar, pero soporte debe evaluar ese archivo; no se reutilizan métricas de otro modelo |
| El historial está vacío | Primero pulsa Clasificar. Si ya lo hiciste, abre el enlace del historial original; otro enlace puede corresponder a un historial distinto |
| El historial se pierde en una instalación local | Sin almacenamiento persistente se conserva solo durante la sesión. Descarga los resultados antes de cerrarla o consulta a soporte |
| No aparece el gráfico de comparación | Selecciona al menos dos predicciones en Historial y comparación |
| El CSV se abre en una sola columna | Usa la opción de importar texto/CSV con separador **punto y coma** y codificación **UTF-8**, o descarga el informe Excel |
| No ves las descargas o el gráfico completo | Desplázate por la página y por la tabla; en pantallas pequeñas algunos elementos quedan más abajo |
| El navegador no abre `http://redmine:3000` | Es una dirección interna de Docker. Desde tu computadora, abre `http://185.208.207.203:3000/` |
| El enlace del ticket pide iniciar sesión o no permite verlo | Entra con tu cuenta de Redmine y comprueba con soporte que tenga acceso al proyecto y al ticket |
| Clasifiqué en el portal pero no aparece un ticket | El portal solo prueba el modelo. Para iniciar el flujo de creación, envía una solicitud al buzón de soporte |
| Recibí un aviso de error al procesar el correo | Consulta con soporte si ya existe un ticket antes de reenviar. Indica la hora aproximada y el asunto del correo |
| No recibí un aviso de cambio de estado | Comprueba con soporte el campo Correo del solicitante y el historial del flujo. La primera observación no envía aviso; debe detectarse un cambio posterior |

Para informar un fallo, utiliza el correo del apartado 6. Incluye los pasos y el mensaje de error, sin claves ni contenido confidencial.

## 5. FAQ (preguntas frecuentes)

**¿Necesito una cuenta para probar el portal?**

El portal actual no tiene inicio de sesión. El enlace del historial permite acceder a sus registros, por lo que debes conservarlo en privado.

**¿Qué modelo conviene usar?**

El de 300 es la referencia del proyecto. Los de 10, 100 y 200 sirven para comparar; más datos o más confianza no garantizan acertar cada correo.

**¿Puedo escribir en inglés?**

La pantalla puede mostrarse en inglés, pero el entrenamiento usa español. Prueba con texto español o con los ejemplos incluidos.

**¿El portal lee adjuntos o crea tickets?**

No. Este formulario clasifica título y descripción. El procesamiento de correo, adjuntos y tickets pertenece al flujo separado de n8n.

**¿Cambiar de modelo borra el historial?**

No. Se limpia el resultado anterior y puedes volver a clasificar el mismo texto. Las predicciones ya guardadas siguen disponibles para comparar.

**¿La confianza es el porcentaje de aciertos del modelo?**

No. Es la probabilidad estimada para esa entrada. Accuracy y F1 se calculan con datos etiquetados y pertenecen a una evaluación concreta.

**¿Puedo recuperar una predicción borrada?**

No desde la interfaz. Borrar historial elimina sus registros; conserva antes una descarga si la necesitas.

**¿Dónde se procesan mis datos?**

En el VPS cuando usas el portal desplegado, o en tu computadora si lo ejecutas localmente. Streamlit no envía esas predicciones a OpenAI ni a NexpAPI. El historial y las descargas sí pueden conservar el texto ingresado.

## 6. Información de contacto para soporte

- **Responsable:** María Quito Castillo, líder del proyecto y desarrolladora full stack.
- **Correo:** [maelizabethquito@uees.edu.ec](mailto:maelizabethquito@uees.edu.ec).
- **Repositorio de referencia:** [ProyectoIA](https://github.com/n8nmquito/ProyectoIA).

Al escribir, indica el problema, los pasos para reproducirlo, el modelo seleccionado, la fecha aproximada y el mensaje de error. Puedes adjuntar una captura con datos ficticios o anonimizados. **No envíes contraseñas, tokens ni correos reales con información sensible.**

## 7. Enviar una solicitud y seguir el ticket

### Enviar el correo

Envía la solicitud a **n8n.mquito@gmail.com**. Escribe un asunto que identifique el problema, el sistema afectado, qué ocurre y qué ayuda necesitas. Por ejemplo: «Usuario bloqueado en JDE» y «No puedo iniciar sesión con mi usuario; aparece un mensaje de bloqueo. Solicito revisar el acceso». Adjunta una captura o un archivo útil para el diagnóstico si corresponde.

![Ejemplo de solicitud enviada al buzón de soporte](../documentacion/imagenes/flujo/01_enviar_correo.png)

El workflow publicado recibe el correo por IMAP y lo procesa automáticamente. El solicitante no necesita entrar en n8n. El flujo limpia el texto, consulta la categoría Python, analiza la solicitud con OpenAI y valida los datos antes de crear la petición. Los adjuntos seleccionados pueden enviarse al agente y los originales se conservan para Redmine; no se anonimizan automáticamente.

### Leer la respuesta

Si se crea el ticket y los filtros permiten el envío, recibirás un correo con su número y enlace. Conserva ese número para consultar el caso.

![Confirmación de ejemplo con el número y enlace del ticket](../documentacion/imagenes/flujo/14_confirmacion_ticket.png)

Si el mensaje informa que no se pudo completar el procesamiento, consulta con soporte si ya existe un ticket antes de reenviar. Un aviso de correo omitido indica que el flujo consideró que el contenido no correspondía a soporte; si necesitas ayuda técnica, envía una solicitud concreta con el sistema afectado y el problema.

### Consultar Redmine

1. Abre el enlace recibido o entra en [Redmine](http://185.208.207.203:3000/).
2. Inicia sesión con la cuenta autorizada para consultar tus tickets.
3. Selecciona el proyecto **Tickets de novedades**, si tu cuenta tiene acceso.
4. En **Peticiones**, busca por el número de ticket o el asunto. Puedes consultar los tipos **Soporte** y **Errores** y ajustar los filtros.
5. Abre el ticket para revisar estado, prioridad, categoría, responsable, descripción y adjuntos. El equipo de soporte gestiona su atención y actualiza el estado.

![Lista de peticiones en Redmine](../documentacion/imagenes/flujo/18_lista_tickets.png)

Los números y resultados de las capturas corresponden a distintas pruebas. La [documentación completa de la interfaz](../../README.md#uso-del-flujo-completo-de-correo-a-redmine) incluye las pantallas de n8n, la configuración de los nodos y una captura histórica con una discrepancia de categoría. El flujo vigente conserva la categoría final de Python.

### Recibir cambios de estado

El workflow **Mquito | Avisos de cambios de estado Redmine** consulta cada minuto los tickets del proyecto configurado y compara su estado con el último observado. Utiliza la dirección del campo **Correo del solicitante**. La primera observación se guarda sin enviar un aviso; cuando después detecta un cambio y la dirección es válida, prepara la notificación.

![Aviso de ejemplo con el cambio de estado de Nueva a Resuelta](../documentacion/imagenes/flujo/20_aviso_cambio_estado.png)

El aviso incluye número, asunto, estado anterior, nuevo estado y enlace. Este proceso no utiliza IA ni modifica los tickets. Los cambios que ocurran y se reviertan entre dos consultas pueden no detectarse. Ver los [detalles del seguimiento](../../workflows/status-notifications/README.md).

### Revisar una ejecución como operador

Si tienes una cuenta autorizada, abre [n8n](http://185.208.207.203:5678) y entra en **Executions**. Localiza la ejecución por su fecha y workflow, revisa los nodos con errores y comprueba **Resultado del ticket**. El estado `success` también puede incluir una omisión controlada y no demuestra por sí solo que se haya creado una petición. Antes de reintentar, verifica el número en Redmine.

Consulta la [guía de configuración](../../workflows/GUIA_CONFIGURACION.md) para credenciales, validaciones y diagnóstico. El acceso a n8n corresponde al operador; el solicitante utiliza el correo y Redmine según sus permisos.

## 8. Direcciones de acceso y red interna

Las capturas muestran dos formas de acceder a los mismos servicios: desde el navegador del usuario y desde los contenedores del servidor. Usa la dirección correspondiente al lugar desde el que te conectas.

| Servicio | Dirección para el usuario | Conexión dentro de Docker |
|---|---|---|
| Redmine | [http://185.208.207.203:3000/](http://185.208.207.203:3000/) | `http://redmine:3000`; n8n consulta catálogos, sube adjuntos y crea tickets por la API |
| n8n | [http://185.208.207.203:5678](http://185.208.207.203:5678) | `http://n8n:5678`, cuando otro contenedor de la red necesita conectarse al servicio |
| Portal Python | [http://185.208.207.203:8501](http://185.208.207.203:8501) | Ejecuta el modelo directamente en su propio contenedor |
| NexpAPI | Sin dirección pública para el usuario | `http://nexpapi:8000/predict`; n8n consulta el clasificador con su credencial |
| PostgreSQL | Sin interfaz web propia | `postgres:5432`; conexión de los servicios o nodos autorizados a la base de datos |

Los servicios de automatización comparten la red Docker **`correo-tickets_automatizacion`**. En esa red, Docker reconoce nombres de servicio como `redmine`, `n8n`, `nexpapi` y `postgres`. La red interna permite la comunicación entre contenedores; el acceso desde el navegador usa la IP del servidor y el puerto publicado.

**Ejemplo:** el nodo de n8n utiliza `POST http://redmine:3000/issues.json` para crear la petición. El usuario consulta el resultado con una dirección como `http://185.208.207.203:3000/issues/54`. Ambas se refieren al mismo Redmine desde lugares distintos. No escribas `http://redmine:3000` en el navegador de tu computadora: normalmente ese nombre solo funciona dentro de la red Docker.

`localhost` siempre se refiere al entorno desde el que se usa. En el navegador de tu computadora es tu propio equipo; en el contenedor de n8n es ese contenedor. Por eso `http://localhost:8501` sirve para el portal si lo ejecutaste localmente, pero no abre el portal remoto del servidor. Dentro del nodo de n8n, utiliza `redmine:3000` para conectarte a Redmine, sin reemplazarlo por `localhost`.

La red interna no reemplaza las credenciales: n8n necesita la clave API de Redmine, NexpAPI requiere su propia clave y el usuario necesita permisos para consultar tickets. No hace falta modificar los nodos ni las direcciones internas para seguir el recorrido como solicitante.
