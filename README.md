# Mquito Ticket

![Python 3.10 y 3.11](https://img.shields.io/badge/Python-3.10%20%7C%203.11-blue)
[![Licencia MIT del código Python](https://img.shields.io/badge/License-MIT-green)](python/LICENSE)
![Interfaz Streamlit](https://img.shields.io/badge/Interfaz-Streamlit-red)
![Estado del proyecto](https://img.shields.io/badge/Estado-piloto%20implementado-blue)

Mquito Ticket clasifica solicitudes de soporte TI y automatiza su registro mediante el circuito correo → n8n + IA → Redmine. Incluye un clasificador Python con versiones de 10, 100, 200 y 300 correos, una interfaz Streamlit y una API interna; la versión de 300 es el modelo final elegido. Está orientado a apoyar la derivación inicial de tickets y su supervisión por el equipo de soporte.

## Tabla de contenidos

1. [Encabezado y badges](#mquito-ticket)
2. [Tabla de contenidos](#tabla-de-contenidos)
3. [Descripción del problema](#descripción-del-problema)
4. [Dataset](#dataset)
5. [Metodología](#metodología)
6. [Resultados](#resultados)
7. [Instalación y uso](#instalación-y-uso)
8. [Interfaz de usuario](#interfaz-de-usuario)
9. [Estructura del proyecto](#estructura-del-proyecto)
10. [Consideraciones éticas](#consideraciones-éticas)
11. [Autores y contribuciones](#autores-y-contribuciones)
12. [Licencia](#licencia)
13. [Agradecimientos y referencias](#agradecimientos-y-referencias)
14. [Videos](#videos)

## Descripción del problema

Las mesas de ayuda reciben correos sobre cuentas, errores de aplicaciones, equipos, redes y consultas generales. Leer cada mensaje, identificar su categoría y decidir a quién corresponde atenderlo exige trabajo repetitivo y puede producir derivaciones inconsistentes.

El proyecto propone una clasificación inicial y automatiza la preparación y creación del ticket en Redmine. Su importancia radica en apoyar una atención organizada y permitir revisar las decisiones del sistema. La reducción de tiempos y los beneficios económicos son objetivos: todavía no se han medido.

Los usuarios objetivo son operadores de mesa de ayuda, personal de soporte TI y responsables que supervisan la asignación de solicitudes. La consola y Streamlit también permiten demostrar y evaluar el clasificador en el contexto académico.

## Dataset

### Descripción y características

La fuente principal es `python/data/raw/correos.json`: un corpus de **300 correos simulados en español** sobre soporte TI. Cada registro contiene:

| Variable | Tipo | Función |
|---|---|---|
| `titulo` | Texto | Asunto de la solicitud; entrada del modelo |
| `cuerpo` | Texto | Descripción de la solicitud; entrada del modelo |
| `clasificacion` | Categoría | Etiqueta utilizada en entrenamiento y evaluación |

| Categoría | Correos |
|---|---:|
| accesos | 70 |
| aplicaciones | 90 |
| infraestructura | 70 |
| otros | 70 |
| **Total** | **300** |

Se conservan datasets anidados de 10, 100, 200 y 300 registros y un modelo para cada tamaño. Los conjuntos pequeños están contenidos en los mayores. Además, existen **25 correos sin etiquetas** en `python/data/test/correos_test_25.json`, separados del entrenamiento, para comparar predicciones y confianza.

### Fuente y licencia

Los 100 correos iniciales fueron aportados por el usuario y se añadieron 200 ejemplos ficticios para ampliar el corpus. No se presentan como solicitudes reales. El corpus maestro y los cuatro datasets de entrenamiento se incluyen en Git por indicación de la responsable del proyecto; los modelos `.pkl` siguen excluidos.

La [licencia MIT del código Python](python/LICENSE) no se extiende automáticamente a los datos. El [corpus maestro](python/data/raw/correos.json) y los [datasets de entrenamiento](python/data/train/) están incluidos en el repositorio. Los modelos y los archivos de particiones procesadas siguen requiriendo copias locales. Consultar el [análisis de datos](python/docs/analisis_datos.md) y la [descripción de los datasets](python/data/README.md).

## Metodología

### Modelo y justificación

El problema se aborda como clasificación supervisada multiclase de texto. Se comparan un baseline que predice la clase mayoritaria, regresión logística y SVM lineal calibrada, usando una representación **TF-IDF de palabras y pares de palabras**.

La SVM calibrada se selecciona por su desempeño en F1 macro durante la comparación y porque permite obtener probabilidades para apoyar la revisión de predicciones. La diferencia frente a la regresión logística optimizada es pequeña y no demuestra superioridad estadística. El artefacto final elegido es `modelo_clasificador_300.pkl`; las otras tres versiones se conservan para comparación.

### Preprocesamiento

1. Validar campos, tipos, etiquetas, límites de longitud y presencia de texto.
2. Normalizar Unicode y HTML, convertir a minúsculas y reemplazar enlaces, correos, IP, ciertos nombres de archivos y números largos.
3. Eliminar signos y espacios repetidos, y combinar título con cuerpo.
4. Detectar etiquetas contradictorias para textos iguales y eliminar duplicados.
5. Ajustar TF-IDF dentro del pipeline y de cada partición de validación, evitando aprender el vocabulario de la partición evaluada.

### Optimización y evaluación

Se utiliza `GridSearchCV` con validación cruzada estratificada de cuatro particiones y semilla 42. La búsqueda explora `C`, `class_weight` y `min_df`; se complementa con análisis de sensibilidad e interacción de hiperparámetros. La SVM utiliza calibración sigmoide interna de dos particiones.

La métrica principal es **F1 macro**, que da el mismo peso a las cuatro categorías. También se informa accuracy, precisión, recall, F1 por clase y matriz de confusión; log loss y Brier multiclase permiten examinar las probabilidades.

La selección histórica utiliza 280 correos y reserva 20 originales para diagnóstico. Después se ajusta el modelo final con los 300 registros. La evaluación por tamaños es exploratoria: usa ajustes ya seleccionados y conjuntos anidados; no constituye una prueba externa ni una validación anidada de toda la búsqueda.

### Integración operativa

n8n recibe el correo, consulta la API Python y envía la solicitud y los adjuntos seleccionados al agente OpenAI. La predicción Python sirve para comparar con la propuesta del agente, que conserva la decisión final de categoría. Antes de crear el ticket en Redmine se validan proyecto, tipo, categoría, membresía y rol asignable.

<img src="Documentacion/Imagenes/c7f36046-5630-4130-9ed5-a623272a4937.png" alt="Flujo de correo, clasificación Python, agente IA, validaciones y creación de ticket en Redmine" width="760">

El detalle está en la [arquitectura](python/docs/arquitectura.md), la [optimización](python/docs/optimizacion.md) y la [guía del flujo](workflows/README.md).

## Resultados

### Rendimiento del modelo final y comparación por tamaño

Resultados registrados el 27 de octubre de 2026 en [version_evaluation.csv](python/results/metrics/version_evaluation.csv). Las cifras de CV provienen de volver a entrenar el pipeline en cada partición; no son una evaluación independiente del archivo final ya ajustado con todos los datos.

| Correos | Accuracy CV | F1 macro CV | F1 macro baseline CV | Casos para revisar de 25 |
|---:|---:|---:|---:|---:|
| 10 | No viable | No viable | No viable | 22 |
| 100 | 0.9200 | 0.9201 | 0.0968 | 2 |
| 200 | 0.9450 | 0.9442 | 0.0968 | 1 |
| **300 — modelo final elegido** | **0.9533** | **0.9543** | **0.1154** | **2** |

En el conjunto de 10, algunos folds dejan menos de dos registros por clase para la calibración interna; por eso no se fuerza una cifra de CV. El F1 de entrenamiento de la versión de 300 es 1.0000 y su accuracy de entrenamiento es 1.0000; estas cifras describen ejemplos conocidos y no miden generalización.

![Comparación de rendimiento por tamaño del modelo](python/documentacion/imagenes/comparacion_modelos_cv.png)

### Diagnóstico histórico sobre 20 correos

| Modelo evaluado sobre los mismos 20 casos | Accuracy | F1 macro |
|---|---:|---:|
| Baseline mayoritario | 0.4500 | 0.1552 |
| SVM calibrada entrenada con 280 correos | 0.9500 | 0.9511 |

La SVM obtiene 19 aciertos y un error. Esta evaluación corresponde al modelo diagnóstico de 280 registros, **no al modelo final de 300**, que posteriormente aprendió también de esos 20 casos. Fuentes: [métricas diagnósticas](python/results/metrics/test_metrics.json) y [baseline](python/results/metrics/baseline_test_metrics.json).

Los 25 correos adicionales no tienen respuestas esperadas: producen predicciones y confianza, pero no accuracy ni F1. Son casos conocidos de regresión y no demuestran ausencia de sobreajuste ni generalización a correo real. La [evaluación y pruebas](python/docs/evaluacion_pruebas.md) detalla estas limitaciones.

## Instalación y uso

### Portal Streamlit con Docker Compose

Desde la raíz del repositorio, con las cuatro copias del modelo en `python/models/`:

```bash
cd python
docker compose up -d --build --wait
docker compose ps
```

El portal escucha en el puerto `8501` y se reinicia con Docker. En el VPS se
ejecuta desde `/mquito/mquito-ticket/python`. Los modelos se montan en modo
solo lectura; el corpus y las credenciales no se incluyen en la imagen.
Esta aplicación no modifica la API que utiliza n8n.

```bash
docker compose logs --tail=100 streamlit
docker compose stop
docker compose start
```

Para cambiar el puerto del host, usar `STREAMLIT_PORT=8502 docker compose up -d`.

### Requisitos del sistema

- Git y Python 3.10 o 3.11 para consola y Streamlit; CPU y almacenamiento para dependencias, datos y modelos. No se requiere GPU y no hay mínimos medidos de RAM o disco.
- Copias locales de los modelos en `python/models/` y del manifiesto de particiones para las operaciones que lo utilicen. El corpus y los cuatro datasets de entrenamiento sí están incluidos en Git.
- Para la automatización: servidor Linux con Docker Engine y Docker Compose v2, acceso al buzón y credenciales de OpenAI y Redmine.

### Instalación local en Windows

1. Descargar el proyecto con una cuenta autorizada y entrar en la carpeta Python:

   ```cmd
   git clone https://github.com/n8nmquito/ProyectoIA.git
   cd ProyectoIA\python
   ```

2. Crear un entorno virtual e instalar las dependencias:

   ```cmd
   py -3.10 -m venv .venv
   .venv\Scripts\activate
   python -m pip install -r requirements.txt
   ```

3. Colocar las copias privadas `modelo_clasificador_10.pkl`, `modelo_clasificador_100.pkl`, `modelo_clasificador_200.pkl` y `modelo_clasificador_300.pkl` en `models/`. El JSON de 25 correos ya está incluido en `data/test/correos_test_25.json`.
4. Ejecutar la interfaz:

   ```cmd
   python -m streamlit run app/app.py --server.address 127.0.0.1
   ```

En Linux, desde `python/`, crear el entorno con `python3 -m venv .venv` y activarlo con `. .venv/bin/activate`; después usar los mismos comandos `python -m pip` y `python -m streamlit`.

### Comandos y ejemplos de uso

Desde `python/`, comparar predicciones de los modelos sobre los 25 correos:

```cmd
python evaluar_nuevos.py --model 100
python evaluar_nuevos.py --model 300
```

Seleccionar otro archivo JSON sin etiquetas y un directorio de salida:

```cmd
python evaluar_nuevos.py --model 300 --data data/test/correos_test_25.json --output results/ejemplo_300
```

Cada entrada del JSON utiliza este formato:

```json
[
  {
    "titulo": "No puedo acceder a mi cuenta",
    "cuerpo": "Al iniciar sesión aparece un mensaje de acceso denegado."
  }
]
```

El comando muestra la categoría propuesta, la confianza y las solicitudes que requieren revisión. Los resultados no son etiquetas verificadas por una persona.

Para reproducir entrenamiento y evaluación, se necesitan además el corpus y el manifiesto privado de particiones descritos en la [documentación de datos](python/data/README.md):

```cmd
python -m src.train
python -m src.train_versions
python -m src.export_datasets
python -m src.evaluate
python -m src.evaluate_versions
python -m pytest -q
```

Reentrenar sustituye los modelos de los mismos nombres; conservar las versiones anteriores si se necesitan para comparación.

### Automatización con Docker en Linux

Los comandos siguientes se ejecutan en un servidor Linux con Git, Python 3,
Docker Engine y Docker Compose v2. Docker debe estar iniciado y el usuario
debe tener permiso para ejecutar sus comandos. Python dentro del contenedor
se instala al construir la imagen; no hace falta instalar sus dependencias
en el servidor.

#### Paso 1. Descargar el proyecto

```bash
git clone https://github.com/n8nmquito/ProyectoIA.git
cd ProyectoIA
```

El repositorio es privado: GitHub debe reconocer una cuenta con acceso.
Los pasos siguientes parten siempre de esta carpeta, donde está
`docker-compose.yml`.

#### Paso 2. Crear y completar el archivo `.env`

Si no existe, crear **`ProyectoIA/.env`**, junto a `docker-compose.yml`,
copiando la plantilla incluida:

```bash
cp .env.example .env
chmod 600 .env
nano .env
```

Si ya existe un `.env` de la instalación, conservarlo y editarlo; no repetir
la copia sobre ese archivo. Puede usarse otro editor en lugar de `nano`.

Este ejemplo contiene únicamente valores ficticios y marcadores que deben
reemplazarse antes de iniciar los servicios:

```dotenv
# IP o DNS del servidor, sin http://, https:// ni puerto
SERVER_HOST=servidor.ejemplo.invalid
BIND_ADDRESS=0.0.0.0
N8N_PORT=5678
REDMINE_PORT=3000
POSTGRES_PORT=5432

# Acceso inicial a las aplicaciones
ADMIN_EMAIL=admin@example.com
REDMINE_ADMIN_USER=admin
ADMIN_PASSWORD='REEMPLAZAR_CON_CLAVE_ADMIN'

# Cuenta administrativa de PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD='REEMPLAZAR_CON_CLAVE_POSTGRES'

# Contraseñas distintas para las cuentas de cada aplicación
N8N_DB_PASSWORD='REEMPLAZAR_CON_CLAVE_BD_N8N'
REDMINE_DB_PASSWORD='REEMPLAZAR_CON_CLAVE_BD_REDMINE'
```

| Campo | Qué completar |
|---|---|
| `SERVER_HOST` | IP o dominio con el que se abrirán n8n y Redmine en el navegador. |
| `BIND_ADDRESS` | Dirección del servidor donde Docker publica los puertos. `0.0.0.0` escucha en todas las interfaces; `127.0.0.1` permite acceso solo desde el propio servidor o mediante un proxy local. |
| `N8N_PORT`, `REDMINE_PORT`, `POSTGRES_PORT` | Puertos libres del servidor. Los ejemplos usan `5678`, `3000` y `5432`. |
| `ADMIN_EMAIL` | Correo del propietario de n8n y del administrador inicial de Redmine. |
| `REDMINE_ADMIN_USER` | Nombre del administrador inicial de Redmine. |
| `ADMIN_PASSWORD` | Contraseña inicial de n8n y Redmine; como máximo 72 bytes por el límite de bcrypt. |
| `POSTGRES_USER` | Administrador de PostgreSQL; debe ser distinto de `n8n` y `redmine`. |
| `POSTGRES_PASSWORD` | Contraseña del administrador de PostgreSQL. |
| `N8N_DB_PASSWORD` | Contraseña de la cuenta `n8n` para su base de datos. |
| `REDMINE_DB_PASSWORD` | Contraseña de la cuenta `redmine` para su base de datos. |

Completar todos los campos del ejemplo. Las contraseñas no deben quedar vacías
ni conservar los marcadores `REEMPLAZAR_...`. Para valores con `$` o `#`, usar
comillas simples como en el ejemplo.

#### Paso 3. Generar la carpeta `.secrets/`

Desde la raíz del proyecto, ejecutar:

```bash
python3 configurar.py
```

El script lee `.env` y crea **`ProyectoIA/.secrets/`** con dos archivos:

| Archivo | Campos que contiene | Cómo se completa |
|---|---|---|
| `.secrets/n8n.env` | `N8N_ENCRYPTION_KEY`, `N8N_INSTANCE_OWNER_PASSWORD_HASH` | El script genera la clave de cifrado y el hash bcrypt de `ADMIN_PASSWORD`. |
| `.secrets/redmine.env` | `SECRET_KEY_BASE` | El script genera la clave interna de Rails. |

Su estructura es la siguiente; los textos entre `<...>` son ilustrativos y
**no deben copiarse como claves o hashes**:

```dotenv
# .secrets/n8n.env — generado por configurar.py
N8N_ENCRYPTION_KEY='<CLAVE_GENERADA_AUTOMATICAMENTE>'
N8N_INSTANCE_OWNER_PASSWORD_HASH='<HASH_BCRYPT_GENERADO_AUTOMATICAMENTE>'
```

```dotenv
# .secrets/redmine.env — generado por configurar.py
SECRET_KEY_BASE='<CLAVE_GENERADA_AUTOMATICAMENTE>'
```

No hace falta crear estos dos archivos a mano. El configurador usa un contenedor
temporal `httpd:2.4-alpine` para calcular bcrypt y lo elimina al terminar.
Los archivos se guardan con permisos `600` y la carpeta nueva con `700`.

Para una instalación existente, recuperar primero sus archivos `.env` y
`.secrets/` desde una copia privada. El configurador conserva las claves de
cifrado que ya encuentre. Conservar especialmente `N8N_ENCRYPTION_KEY`:
n8n la necesita para descifrar sus credenciales guardadas.

#### Paso 4. Levantar PostgreSQL, n8n y Redmine

```bash
docker compose config --quiet
docker compose build --pull
docker compose up -d
docker compose ps
docker compose logs --tail=50 postgres n8n redmine
```

PostgreSQL crea las bases `n8n` y `redmine` con sus usuarios la primera vez,
cuando el volumen está vacío. n8n y Redmine esperan a que PostgreSQL esté
disponible. El primer arranque puede tardar varios minutos por las migraciones.

| Servicio | Acceso con los puertos del ejemplo | Usuario y contraseña |
|---|---|---|
| n8n | `http://IP_O_DOMINIO:5678` | `ADMIN_EMAIL` y `ADMIN_PASSWORD`. |
| Redmine | `http://IP_O_DOMINIO:3000` | `REDMINE_ADMIN_USER` y `ADMIN_PASSWORD`, en una instalación nueva. |
| PostgreSQL | Host `IP_O_DOMINIO`, puerto `5432`, base `n8n` o `redmine` | `POSTGRES_USER` y `POSTGRES_PASSWORD` para administración externa. |

Dentro de Docker, las aplicaciones usan `postgres:5432` con sus cuentas
`n8n` y `redmine`. `localhost` dentro de un contenedor apunta a ese mismo
contenedor. Cambiar contraseñas de PostgreSQL en `.env` después de inicializar
el volumen requiere cambiarlas también en la base. La contraseña inicial de
Redmine tampoco se restablece al editar `.env`.

#### Paso 5. Preparar y levantar el contenedor Python

Este paso requiere disponer de la copia privada del modelo entrenado con
300 correos. Copiarla, sin cambiar su nombre, a:

```text
ProyectoIA/python/models/modelo_clasificador_300.pkl
```

El modelo no está incluido en Git. Sin él, Docker no puede construir esta
imagen; los tres servicios anteriores pueden funcionar de forma independiente.

Crear **`ProyectoIA/.secrets/clasificador.env`** con una clave exclusiva para
la API, de al menos 32 caracteres. Ejemplo ilustrativo:

```dotenv
CLASSIFIER_API_KEY='<CLAVE_ALEATORIA_PROPIA_DE_AL_MENOS_32_CARACTERES>'
```

Para generar el archivo con una clave aleatoria sin mostrarla en la consola,
ejecutar lo siguiente **solo si el archivo todavía no existe**:

```bash
umask 077
python3 -c "import secrets; from pathlib import Path; Path('.secrets/clasificador.env').open('x').write('CLASSIFIER_API_KEY=' + secrets.token_urlsafe(32) + '\n')"
chmod 600 .secrets/clasificador.env
```

La estructura local queda así:

```text
ProyectoIA/
├── .env
├── .secrets/
│   ├── n8n.env
│   ├── redmine.env
│   └── clasificador.env
├── docker-compose.yml
├── docker-compose.python.yml
└── python/
    └── models/
        └── modelo_clasificador_300.pkl
```

Agregar el servicio Python mediante el archivo Compose complementario:

```bash
docker compose -f docker-compose.yml -f docker-compose.python.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.python.yml up -d --build clasificador-python
docker compose -f docker-compose.yml -f docker-compose.python.yml ps
docker compose -f docker-compose.yml -f docker-compose.python.yml logs --tail=50 clasificador-python
```

Comprobar la API desde el propio contenedor:

```bash
docker compose -f docker-compose.yml -f docker-compose.python.yml exec clasificador-python python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health').read().decode())"
```

La respuesta debe indicar `status: ok` y `muestras_entrenamiento: 300`.
La API escucha en el puerto interno `8000`; no se publica un puerto Python
en el servidor. No agregar esta copia si ya existe otro clasificador desplegado
en la misma red con el nombre `clasificador-python`.

#### Paso 6. Conectar n8n con los servicios

En n8n, importar `workflows/correo-ia-redmine-python300.json` y configurar
las credenciales antes de activar el flujo:

| Integración | Qué configurar en n8n |
|---|---|
| Clasificador Python | URL `http://clasificador-python:8000/predict`; credencial Header Auth con nombre `X-API-Key` y valor igual a `CLASSIFIER_API_KEY` de `.secrets/clasificador.env`. |
| Redmine | URL interna `http://redmine:3000`; credencial Header Auth con nombre `X-Redmine-API-Key` y la clave del usuario de integración de Redmine. Crear el proyecto y habilitar sus tipos, categorías y miembros. |
| Correo entrante | Servidor IMAP, puerto, TLS, usuario y contraseña del buzón. |
| OpenAI | Clave API en la credencial del proveedor utilizada por el agente. |
| Correo saliente | Credencial SMTP del buzón que enviará las notificaciones. |

Las claves IMAP, OpenAI, SMTP y Redmine se cargan en **Credentials** de n8n;
no se agregan al JSON del flujo ni a los ejemplos de este README.
El arranque de los contenedores no crea esas credenciales ni activa el flujo.

#### Paso 7. Consultar estado, detener y volver a iniciar

Para los tres servicios de la base:

```bash
docker compose ps
docker compose logs --tail=100 n8n redmine postgres
docker compose stop
docker compose start
```

Si se agregó Python, usar ambos archivos para administrar los cuatro servicios:

```bash
docker compose -f docker-compose.yml -f docker-compose.python.yml ps
docker compose -f docker-compose.yml -f docker-compose.python.yml stop
docker compose -f docker-compose.yml -f docker-compose.python.yml start
```

Los datos persisten en `postgres_data`, `n8n_data` y `redmine_files`, con el
prefijo `correo-tickets_`. Conservar esos volúmenes y respaldar `.env` y
`.secrets/`. `docker compose down -v` elimina los volúmenes y sus datos.

`.env`, `.secrets/` y los modelos están excluidos de Git. Esta configuración
usa HTTP y publica PostgreSQL: está pensada para una red privada o VPN.
Para acceso público, configurar HTTPS y restringir el acceso a los puertos.

## Interfaz de usuario

La aplicación cumple los cinco grupos funcionales: entrada validada de título
y descripción; botón de clasificación con indicador de carga y mensajes de
error; categoría, confianza y gráfico de probabilidades; sección **Acerca de**
con métricas y limitaciones; y botón **Prueba con ejemplo** con cuatro casos.
También incluye diseño adaptable, temas claro/oscuro, interfaz Español/English,
descarga CSV de predicciones, historial persistente de hasta 50 resultados por enlace y
comparación de probabilidades mediante gráficos interactivos Altair. El modelo
sigue entrenado en español; elegir English traduce la interfaz.

La interfaz principal utiliza **Streamlit** y se ejecuta localmente. Presenta el formulario a la izquierda y el resultado a la derecha, con fondo oscuro, tarjetas gris carbón y acentos azules. Permite seleccionar modelos de 10, 100, 200 y 300 correos; el de 300 es el predeterminado.

### Capturas de pantalla

![Formulario de clasificación de solicitudes](python/documentacion/imagenes/app/portal_resultado.png)

![Historial de sesión y comparación de modelos](python/documentacion/imagenes/app/portal_historial.png)

Las capturas muestran el portal actualizado y la comparación de resultados verificados en el VPS.

### Instrucciones de uso

1. Iniciar Streamlit con el comando de instalación y abrir [la interfaz local](http://127.0.0.1:8501).
2. Elegir el tamaño del modelo en el selector de clasificación.
3. Escribir el título y el cuerpo de la solicitud, o cargar un ejemplo.
4. Ejecutar la clasificación y revisar la categoría, la confianza y las cuatro probabilidades.
5. Atender las advertencias de revisión y consultar la vista «Acerca de» para interpretar el resultado. Al cambiar de modelo se conserva el texto y se borra el resultado anterior para volver a clasificarlo.

La interfaz valida entradas y muestra estados de procesamiento y errores. No crea tickets; la automatización de correo funciona como componente separado. Consultar el [manual de usuario](python/docs/manual_usuario.md).

### Acceso a la aplicación desplegada

El [portal Streamlit del VPS](http://185.208.207.203:8501) se despliega con `python/compose.yaml`. El formulario enviado a ese portal se procesa en el VPS; la ejecución local sigue disponible. La automatización utiliza [n8n](http://185.208.207.203:5678) y [Redmine](http://185.208.207.203:3000), con sus credenciales y permisos. La API Python de n8n permanece en la red interna Docker. El portal usa HTTP y no incorpora autenticación; utilizar ejemplos sin información sensible.

## Estructura del proyecto

| Carpeta principal | Contenido |
|---|---|
| `python/` | Proyecto actual del clasificador, configuración, dependencias y lanzador local |
| `python/src/` | Preparación de datos, entrenamiento, optimización y evaluación |
| `python/app/` | Interfaz Streamlit, presentación y estilos |
| `python/deploy/` | API Python, contenedor e instrucciones de despliegue |
| `python/data/` | Corpus maestro, datasets por tamaño y casos de prueba incluidos; particiones procesadas y hoja de revisión excluidas de Git |
| `python/models/` | Cuatro modelos guardados y documentación; los archivos `.pkl` permanecen fuera de Git |
| `python/notebooks/` | Notebooks de análisis y experimentación |
| `python/results/` | Métricas, informes y resultados de evaluación |
| `python/tests/` | Pruebas automatizadas del proyecto Python |
| `python/docs/` | Planificación, datos, arquitectura, optimización, ética, manual y evaluación |
| `python/documentacion/imagenes/` | Gráficos y capturas de la aplicación |
| `python/workshop/` | Material de referencia del taller |
| `workflows/` | Flujos importables de n8n, guías, validaciones y notificaciones |
| `n8n/` | Configuración de construcción e inicio de n8n |
| `redmine/` | Configuración de construcción e inicio de Redmine |
| `postgres/` | Inicialización de las bases y usuarios de PostgreSQL |
| `classifier/` | Experimento anterior de TF-IDF y regresión logística integrado con PostgreSQL |
| `correos_simulados/` | Corpus local del experimento inicial, excluido de Git |
| `Documentacion/` | Diagramas y documentos complementarios del proyecto |

En la raíz, `docker-compose.yml` configura los servicios de base, `docker-compose.python.yml` incorpora la API Python y `configurar.py` genera los secretos iniciales. `.env` y `.secrets/` son configuración privada y no se publican.

## Consideraciones éticas

- **Privacidad y permisos:** el corpus y los datasets de entrenamiento se incluyen por indicación de la responsable del proyecto. La licencia de uso de los datos debe distinguirse de la licencia MIT del código. Las credenciales se guardan fuera del código y de las exportaciones del flujo.
- **Sesgos y equidad:** el corpus es pequeño, simulado y de un dominio limitado. Puede representar mal abreviaturas, estilos de redacción y problemas poco frecuentes. No se ha evaluado equidad demográfica.
- **Transparencia:** se muestran probabilidades y advertencias; la confianza no garantiza que una categoría sea correcta. La coincidencia entre Python y el agente tampoco demuestra exactitud.
- **Servicios externos:** el agente OpenAI puede recibir texto del correo, adjuntos seleccionados y respuestas de herramientas de Redmine. La limpieza del clasificador Python no anonimiza el mensaje original enviado al agente.
- **Límites de evaluación:** los datos anidados, los ajustes previamente seleccionados y los casos conocidos restringen la interpretación de las métricas. No hay una validación externa con usuarios finales ni resultados demostrados sobre correo real.
- **Uso inadecuado:** no utilizar predicciones para conceder accesos, sancionar personas, denegar atención o resolver incidentes críticos automáticamente. No introducir contraseñas ni datos personales innecesarios.
- **Supervisión:** en el flujo n8n no existe una aprobación humana obligatoria antes de cada alta. El equipo de soporte debe revisar y corregir asignaciones; antes de usar información real se deben definir acceso, retención, transporte y responsabilidades.

Las medidas y limitaciones se desarrollan en las [consideraciones éticas](python/docs/consideraciones_eticas.md).

## Autores y contribuciones

| Integrante | Rol | Contribución |
|---|---|---|
| **María Quito Castillo** | Líder del Proyecto y Desarrollador TI (desarrolladora full stack) | Liderazgo del proyecto y desarrollo full stack |
| &nbsp; | Data Scientist | &nbsp; |
| &nbsp; | Experto Soporte TI | &nbsp; |
| &nbsp; | Equipo IA | &nbsp; |
| &nbsp; | Soporte TI | &nbsp; |
| &nbsp; | TI | &nbsp; |
| &nbsp; | Mesa de Ayuda | &nbsp; |

<br>

## Licencia

<br><br>

## Agradecimientos y referencias

<br><br>

## Videos

### Video pitch de 5 minutos

Enlace:

<br><br>

### Video de respuestas a las preguntas

Enlace:

<br><br>
