# 📬 Mquito Ticket

Automatización de soporte: **correo → n8n + IA → Redmine**.

Sistema desplegado con clasificador Python de 300 correos, agente OpenAI y
validación de tickets en Redmine. La consola y Streamlit permiten probar también
las versiones de 10, 100 y 200 correos. Ver [proyecto Python](python/README.md).

## 🧩 Qué incluye

| Contenedor | Función | Puerto |
|---|---|---|
| **n8n** | Orquestación de automatizaciones | `5678` |
| **Redmine** | Tickets, con API REST habilitada | `3000` |
| **PostgreSQL** | Bases `n8n` y `redmine`, con usuarios separados | `5432` |

Los tres servicios de la base comparten red Docker y volúmenes. Además existe
un servicio separado clasificador-python en la misma red, sin puerto publicado,
con la API del modelo de 300. Ver [despliegue de la API](python/deploy/DESPLIEGUE_REALIZADO.md).
Desde n8n, Redmine se conecta mediante `http://redmine:3000`.

## 🚀 Inicio rápido

Requisitos: servidor Linux, Python 3, Docker Engine y Docker Compose v2.

```bash
git clone https://github.com/n8nmquito/ProyectoIA.git
cd ProyectoIA
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

- [Datos y restricciones de uso](python/data/README.md): corpus de 300 y
  datasets por tamaño. Los 100 iniciales y sus derivados se mantienen sin
  publicar mientras no se confirme su autorización de redistribución.
- [Clasificador Python TF-IDF + SVM calibrada](python/README.md): cuatro modelos,
  datasets, consola, Streamlit, API y evidencias. `classifier/` conserva el
  experimento anterior y no es el clasificador activo del flujo.
- [Guía simple de nodos y parámetros](workflows/GUIA_CONFIGURACION.md): cómo
  configurar correo, API Python, OpenAI, adjuntos, asignación y activación.
- [Flujo de n8n](workflows/README.md): versión integrada y JSON importable
  inactivo sin credenciales; el flujo existente en el servidor está activo.

- [Despliegue y mantenimiento](DESPLIEGUE.md): instalación, credenciales,
  persistencia, migración desde dos PostgreSQL y comandos de operación.
- [Proceso de automatización](PROCESO_AUTOMATIZACION.md): arquitectura,
  clasificación con IA, asignación, duplicados y pruebas de aceptación.

## 🛠️ Próximos pasos

- Completar la revisión humana de etiquetas de los mismos 25 casos conocidos.
- Mantener sin publicar el corpus inicial mientras no haya autorización.
- Completar la entrega académica y revisar privacidad antes de utilizar datos reales.
- Incorporar control de duplicados y seguimiento de respuestas; ajustar las reglas
  de asignación por proyecto y rol ya implementadas.

**Validación:** flujo probado en el servidor con datos ficticios, Gemini y Redmine,
incluyendo adjuntos y respaldo ante un PDF ilegible. Ver el detalle en la guía del flujo.

## Interfaz web del clasificador

Abrir http://185.208.207.203/. La página clasifica título y descripción con el
modelo Python de 300 correos y muestra sus probabilidades. No utiliza n8n ni
OpenAI y no crea tickets. El flujo de correo descrito arriba continúa separado.
Código y operación: [python/web](python/web/README.md).
