# 📬 Mquito Ticket

Automatización de soporte: **correo → n8n + IA → Redmine**.

Base Docker y flujo de demostración de correo con IA, guardado en n8n y listo
para completar las credenciales y realizar la prueba de integración.

## 🧩 Qué incluye

| Contenedor | Función | Puerto |
|---|---|---|
| **n8n** | Orquestación de automatizaciones | `5678` |
| **Redmine** | Tickets, con API REST habilitada | `3000` |
| **PostgreSQL** | Bases `n8n` y `redmine`, con usuarios separados | `5432` |

Los tres servicios comparten una red Docker y conservan sus datos en volúmenes.
Desde n8n, Redmine se conecta mediante `http://redmine:3000`.

## 🚀 Inicio rápido

Requisitos: servidor Linux, Python 3, Docker Engine y Docker Compose v2.

```bash
git clone https://github.com/jpinero-dev/mquito-ticket.git
cd mquito-ticket
cp .env.example .env
```

Completar `.env`: dirección del servidor, puertos, usuarios y contraseñas.
Si ya tenés el `.env` preparado para esta
instalación, copialo de forma privada en lugar de reemplazarlo con el ejemplo.

```bash
chmod 600 .env
python3 configurar.py
docker compose config --quiet
docker compose build --pull
docker compose up -d
docker compose ps
```

| Aplicación | Acceso | Usuario |
|---|---|---|
| n8n | `http://IP_SERVIDOR:5678` | Correo de `ADMIN_EMAIL` |
| Redmine | `http://IP_SERVIDOR:3000` | `admin` |

Las contraseñas se configuran en `.env`. Ese archivo **no se publica en Git**.
El configurador genera el hash y las claves internas en `.secrets/`, también
excluida de Git. Usa un contenedor temporal de httpd solo para generar bcrypt;
al finalizar siguen siendo tres servicios. Si la instalación ya tiene datos,
conservar y copiar también `.secrets/` antes de ejecutar el configurador.
HTTP está pensado para red privada o VPN; para acceso público, configurar HTTPS.

## 📖 Documentación

- [Configurar el flujo de n8n](workflows/README.md): credenciales pendientes,
  prueba manual y activación; incluye el JSON importable sin secretos.

- [Despliegue y mantenimiento](DESPLIEGUE.md): instalación, credenciales,
  persistencia, migración desde dos PostgreSQL y comandos de operación.
- [Proceso de automatización](PROCESO_AUTOMATIZACION.md): arquitectura,
  clasificación con IA, asignación, duplicados y pruebas de aceptación.

## 🛠️ Próximos pasos

- Conectar el buzón de soporte.
- Crear proyecto, categorías y equipos en Redmine.
- Probar el flujo con un correo real y sus adjuntos; la prueba manual con Gemini ya pasó.
- Incorporar control de duplicados, asignación por reglas y seguimiento de respuestas.

**Validación:** flujo probado en el servidor con datos ficticios, Gemini y Redmine,
incluyendo adjuntos y respaldo ante un PDF ilegible. Ver el detalle en la guía del flujo.
