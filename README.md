# Mquito Ticket

Automatización de soporte: **correo → n8n + IA → Redmine**.

Sistema desplegado con clasificador Python de 300 correos, agente OpenAI y
validación de tickets en Redmine. La consola y Streamlit permiten probar también
las versiones de 10, 100 y 200 correos. Ver [proyecto Python](python/README.md).

## Qué incluye

| Contenedor | Función | Puerto |
|---|---|---|
| **n8n** | Orquestación de automatizaciones | `5678` |
| **Redmine** | Tickets, con API REST habilitada | `3000` |
| **PostgreSQL** | Bases `n8n` y `redmine`, con usuarios separados | `5432` |
| **clasificador-python** | API del modelo Python de 300 correos | `8000`, solo dentro de Docker |

`docker-compose.yml` levanta los tres servicios de la base.
`docker-compose.python.yml` agrega el clasificador a la misma red, sin publicar
su puerto en el servidor. Desde n8n, Redmine responde en `http://redmine:3000`
y el clasificador en `http://clasificador-python:8000`.

## Flujo de automatización

n8n recibe el correo y conserva sus adjuntos. Consulta el clasificador Python,
envía la solicitud al agente OpenAI y compara las categorías propuestas.
Para las solicitudes de soporte, prepara y valida el ticket antes de crearlo
en Redmine y enviar la notificación correspondiente.

<img src="Documentacion/Imagenes/c7f36046-5630-4130-9ed5-a623272a4937.png" alt="Flujo actual: correo IMAP, clasificación Python, agente OpenAI, validaciones, adjuntos y creación del ticket en Redmine" width="560">

El detalle de los nodos y la exportación importable están en la
[guía del flujo](workflows/README.md).

## Clasificador Python

El clasificador transforma título y cuerpo mediante TF-IDF y utiliza una SVM
calibrada para proponer accesos, aplicaciones, infraestructura u otros.
Se conservan versiones de 10, 100, 200 y 300 correos; la de 300 es la elegida
para el despliegue. Su predicción sirve para comparar con la decisión del agente.

![Preparación de datos, representación TF-IDF, entrenamiento de la SVM, validación y guardado del modelo](Documentacion/Imagenes/c6c1e33b-e22a-4d55-a79f-d2438501b3dc.png)

La metodología, las métricas y sus límites se explican en el
[proyecto Python](python/README.md). El corpus y los modelos se conservan
fuera de Git mientras no se autorice su redistribución.

## Agente de IA y validaciones

El agente analiza el asunto, el mensaje y los adjuntos seleccionados.
Propone categoría, prioridad, proyecto, tipo de ticket y responsable a partir
de las consultas a Redmine. Los nodos posteriores verifican proyecto, tipo,
categoría, membresía y rol antes de crear el ticket.

![Análisis del correo por el agente: recepción, interpretación, propuesta de asignación y explicación del resultado](Documentacion/Imagenes/Agente.png)

Las herramientas del agente consultan proyectos, miembros, tipos de ticket,
roles y la cuenta de integración mediante peticiones GET.

<details>
<summary>Consultas del agente a la API de Redmine</summary>

![Consultas GET del agente a proyectos, membresías, tipos de ticket, roles y cuenta de integración](Documentacion/Imagenes/Apis%20Agente.png)

</details>

La configuración de los nodos y las credenciales se describe en la
[guía de configuración](workflows/GUIA_CONFIGURACION.md).

## Instalación y arranque de los contenedores

Los comandos siguientes se ejecutan en un servidor Linux con Git, Python 3,
Docker Engine y Docker Compose v2. Docker debe estar iniciado y el usuario
debe tener permiso para ejecutar sus comandos. Python dentro del contenedor
se instala al construir la imagen; no hace falta instalar sus dependencias
en el servidor.

### 1. Descargar el proyecto

```bash
git clone https://github.com/n8nmquito/ProyectoIA.git
cd ProyectoIA
```

El repositorio es privado: GitHub debe reconocer una cuenta con acceso.
Los pasos siguientes parten siempre de esta carpeta, donde está
`docker-compose.yml`.

### 2. Crear y completar el archivo `.env`

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

### 3. Generar la carpeta `.secrets/`

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

### 4. Levantar PostgreSQL, n8n y Redmine

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

### 5. Preparar y levantar el contenedor Python

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

### 6. Conectar n8n con los servicios

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

### 7. Consultar estado, detener y volver a iniciar

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

## Próximos pasos

- Completar la revisión humana de etiquetas de los mismos 25 casos conocidos.
- Mantener sin publicar el corpus inicial mientras no haya autorización.
- Completar la entrega académica y revisar privacidad antes de utilizar datos reales.
- Incorporar control de duplicados y seguimiento de respuestas; ajustar las reglas
  de asignación por proyecto y rol ya implementadas.

**Validación:** flujo probado en el servidor con datos ficticios, Gemini y Redmine,
incluyendo adjuntos y respaldo ante un PDF ilegible. Ver el detalle en la guía del flujo.

## Interfaz local del clasificador

Streamlit permite probar el clasificador en el navegador sin crear tickets.
Esta interfaz es opcional y se ejecuta fuera de los contenedores anteriores.
Requiere los modelos privados correspondientes en `python/models/`.

Desde la raíz del proyecto, en Linux:

```bash
cd python
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app/app.py --server.address 127.0.0.1
```

Abrir `http://127.0.0.1:8501` en el navegador del equipo donde se ejecutó
Streamlit. Las instrucciones para Windows y el uso de la aplicación están
en el [proyecto Python](python/README.md).
