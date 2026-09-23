# n8n + Redmine para automatizar correos y tickets

El diseño funcional, los pendientes, las etapas de implementación y las pruebas
están en [PROCESO_AUTOMATIZACION.md](PROCESO_AUTOMATIZACION.md).

Estructura para copiar a un servidor Linux con Python 3, Docker Engine y Docker Compose v2.
Incluye n8n, Redmine y un único contenedor PostgreSQL con dos bases independientes
(`n8n` y `redmine`), cada una con su propio usuario. Los tres servicios
comparten la red `correo-tickets_automatizacion`. Las bases no publican puertos.

## Instalación en el servidor

1. Copiar esta carpeta completa, incluyendo `.env` y `.secrets/` si ya existen.
   Para una instalación nueva desde Git, copiar `.env.example` a `.env`.
2. Editar `.env`: cambiar `SERVER_HOST=localhost` por la IP o DNS del servidor,
   sin protocolo ni puerto. Cambiar `ADMIN_EMAIL` por un correo propio si corresponde.
3. Desde la carpeta copiada, ejecutar:

```bash
chmod 600 .env
python3 configurar.py
docker compose config --quiet
docker compose build --pull
docker compose up -d
docker compose ps
docker compose logs -f n8n redmine
```

`build` construye las tres imágenes; `up -d` inicia los servicios.
El primer arranque puede tardar varios minutos por las migraciones.

PostgreSQL crea ambas bases y sus usuarios mediante `postgres/init-databases.sh`
solo cuando el volumen `postgres_data` está vacío. Las aplicaciones usan el host
`postgres` y no tienen permisos de superusuario. `POSTGRES_USER` y
`POSTGRES_PASSWORD` en `.env` corresponden a la cuenta administrativa de PostgreSQL.
Las cuentas de aplicación son `n8n` y `redmine`, con sus claves respectivas
`N8N_DB_PASSWORD` y `REDMINE_DB_PASSWORD`. El puerto interno es 5432;
PostgreSQL no publica un puerto hacia Internet.

**Si ya desplegaste la configuración anterior con dos contenedores de bases:**
este cambio no migra sus datos automáticamente. Antes de reemplazarla, detener
las aplicaciones y respaldar ambas bases con `pg_dump`. Conservar los volúmenes
anteriores `correo-tickets_n8n_db` y `correo-tickets_redmine_db`, el volumen de n8n,
los adjuntos, `.env` y `.secrets/`. Iniciar solo el nuevo servicio `postgres`, restaurar cada
respaldo en su base correspondiente y verificar los datos antes de iniciar las
aplicaciones. No eliminar los volúmenes anteriores hasta comprobar la migración.
Los comandos de instalación de arriba están destinados a una instalación nueva.

## Acceso inicial

| Aplicación | Dirección | Usuario | Contraseña |
|---|---|---|---|
| n8n | `http://IP_SERVIDOR:5678` | `ADMIN_EMAIL` | Definida en `.env` |
| Redmine | `http://IP_SERVIDOR:3000` | `admin` | Definida en `.env` |

n8n requiere un email como identificador. Se aprovisiona el propietario mediante
las variables oficiales de n8n y un hash bcrypt generado desde `ADMIN_PASSWORD`.
`python3 configurar.py` prepara ese hash y las claves internas en `.secrets/`.
Para actualizar la clave de n8n, editar `.env`, ejecutar el configurador y luego
`docker compose up -d`. Las claves de cifrado existentes se conservan.
Al migrar desde el formato anterior, el configurador también puede recuperar las
claves internas del viejo `.env`; no borrarlas antes de ejecutar esa migración.
El parser admite líneas `CLAVE=valor` y valores entre comillas, sin expansión
de variables. Para contraseñas con `$` o `#`, usar comillas simples en `.env`.

Redmine configura el administrador, los datos iniciales en español y la API REST
antes de iniciar el servidor web. La marca `files/.admin-bootstrap-v1` evita
restablecer la contraseña en cada reinicio. Cambiar `ADMIN_PASSWORD` posteriormente
no modifica una cuenta de Redmine ya inicializada; usar su interfaz para eso.
El usuario inicial de Redmine se define con `REDMINE_ADMIN_USER`; modificarlo
en `.env` tampoco renombra una cuenta ya inicializada.

Esta configuración publica HTTP para una red privada o VPN. Para acceso desde
Internet, configurar HTTPS con un proxy y ajustar en Compose `N8N_PROTOCOL`,
`N8N_EDITOR_BASE_URL`, `WEBHOOK_URL`, `N8N_SECURE_COOKIE=true` y
`N8N_PROXY_HOPS` según la cantidad de proxies. Restringir los puertos publicados
al acceso previsto. Para recuperar contraseñas por correo se requiere SMTP;
SMTP no está configurado.

## Comunicación y próxima automatización

Desde n8n, la dirección de Redmine es **`http://redmine:3000`**.
Desde Redmine, n8n está disponible en `http://n8n:5678`.
Usar los nombres de servicio: `localhost` dentro de un contenedor apunta a él mismo.

La API REST de Redmine queda habilitada. Para la próxima etapa:

1. Crear un proyecto en Redmine y un usuario para la integración con permisos
   para crear peticiones en ese proyecto.
2. Obtener la clave API desde «Mi cuenta» de ese usuario.
3. En n8n, configurar Redmine con la URL interna y esa clave API.
4. Configurar el acceso al buzón (IMAP, Gmail o Microsoft 365) y luego el flujo
   correo → ticket, incluyendo control de duplicados.

El buzón, el proyecto y el flujo no están creados todavía.

Verificar desde el servidor la comunicación interna:

```bash
docker compose exec n8n node -e "fetch('http://redmine:3000/login').then(r=>{console.log('Redmine HTTP',r.status);process.exit(r.ok?0:1)}).catch(e=>{console.error(e);process.exit(1)})"
```

## Datos y mantenimiento

Los volúmenes `postgres_data`, `n8n_data` y `redmine_files` conservan las
bases, la configuración de n8n y los adjuntos de Redmine. Compose les agrega
el prefijo `correo-tickets_`.

```bash
docker compose stop         # detener
docker compose start        # volver a iniciar
docker compose down         # retirar contenedores conservando datos
```

No usar `docker compose down -v` si se necesitan los datos: elimina los volúmenes.
Respaldar ambas bases con `pg_dump`, los adjuntos, el volumen de n8n, `.env` y `.secrets/`.
Conservar `.secrets/n8n.env`: contiene la clave para descifrar las credenciales de n8n.
Las contraseñas de PostgreSQL en `.env` se aplican al inicializar `postgres_data`; editarlas
después requiere también cambiar la contraseña dentro de PostgreSQL.

Las imágenes de aplicación están fijadas en sus Dockerfiles: n8n `2.40.5` y
Redmine `6.1.4-bookworm`; PostgreSQL usa la rama `16-bookworm`.
Actualizar versiones deliberadamente y con respaldo previo.

## Validación realizada

Se verificó la sintaxis YAML, las referencias a variables y Dockerfiles, la red
compartida y que el hash bcrypt corresponde a la contraseña solicitada.
No se construyeron ni ejecutaron contenedores en la máquina de preparación;
la validación de arranque y login queda para el servidor con los comandos anteriores.

Referencias oficiales:

- [Propietario de n8n mediante variables de entorno](https://docs.n8n.io/deploy/host-n8n/configure-n8n/manage-settings-using-environment-variables)
- [Imagen oficial de Redmine](https://hub.docker.com/_/redmine)
