# Tucuman Places Automator

Sistema para obtener, procesar y administrar bares/restaurantes de Tucuman de forma automatizada.

## Stack

- Backend: Python, FastAPI, SQLAlchemy, SQLite
- Frontend: Vite, React, TypeScript
- IA: OpenAI API con fallback local
- Notificaciones: Slack Incoming Webhook opcional
- Deploy: Docker Compose
- Automatizacion: script de ingesta reutilizable por cron, Task Scheduler o n8n

## Funcionalidades

- Scraping no agresivo desde Tucuman Turismo.
- CRUD de lugares.
- Desactivacion logica.
- Clasificacion y descripcion con IA.
- Deteccion de duplicados por normalizacion, similitud y, si hay API key, apoyo de IA.
- Logs de importacion.
- Notificacion Slack con conteos, fallback y muestra de items scrapeados.
- Dashboard simple con metricas.

## Uso local sin Docker

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Importar datos:

```bash
cd backend
python -m app.jobs.import_bars
```

## Uso con Docker

```bash
cp .env.example .env
docker compose up --build
```

Servicios:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

Importar datos dentro del contenedor:

```bash
docker compose exec backend python -m app.jobs.import_bars
```

## Deploy en VPS con dominio

1. Clonar/subir el proyecto al VPS.
2. Crear `.env` desde `.env.example`.
3. Configurar `PUBLIC_API_URL` con el dominio del backend, por ejemplo `https://api.tudominio.com`.
4. Levantar:

```bash
docker compose -f docker-compose.yml up -d --build
```

5. Poner Caddy, Nginx Proxy Manager, Traefik o Nginx delante:
   - `app.tudominio.com` -> `frontend:80`
   - `api.tudominio.com` -> `backend:8000`

El archivo `deploy/Caddyfile.example` deja un ejemplo listo para adaptar.

Variables utiles para deploy:

```bash
OPENAI_API_KEY=tu_api_key
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_SCRAPE_PREVIEW_LIMIT=10
IMPORT_RUN_TOKEN=un_token_largo_y_aleatorio
DATABASE_URL=sqlite:///./data/app.db
VITE_API_URL=https://api.tudominio.com
CORS_ORIGINS=https://app.tudominio.com
```

## Automatizacion

El core automatizable es:

```bash
docker compose exec backend python -m app.jobs.import_bars
```

Si queres disparar la importacion por HTTP desde la UI, n8n o curl, el endpoint `POST /imports/run` requiere:

```bash
Authorization: Bearer $IMPORT_RUN_TOKEN
```

Opciones:

- Cron en VPS: ejecutar cada noche.
- Windows Task Scheduler: ejecutar manual o periodicamente.
- n8n: nodo SSH o Execute Command apuntando al comando anterior.

El flujo recomendado en n8n esta documentado en `deploy/n8n-flow-notes.md`:

1. Cron trigger.
2. SSH al VPS.
3. Ejecutar script de importacion.
4. Leer respuesta/log.
5. Enviar notificacion por Slack/email si hubo error o nuevos registros.

## Como se evitan duplicados

1. Se normaliza nombre y direccion: minusculas, sin acentos, sin signos y sin palabras de relleno.
2. Se busca coincidencia exacta por clave normalizada.
3. Se compara similitud entre nombre+direccion contra registros existentes.
4. Si hay OpenAI API key, se puede pedir una segunda opinion para casos ambiguos.
5. Si parece duplicado, se actualiza el registro existente en vez de crear otro.

## Como escalarlo

- Cambiar SQLite por PostgreSQL/Supabase.
- Mover la ingesta a una cola de trabajos.
- Agregar multiples fuentes.
- Guardar historial de cambios por campo.
- Agregar aprobacion manual antes de publicar datos.
- Usar embeddings para deduplicacion semantica.

## Problemas posibles

- La web fuente puede cambiar su HTML.
- Datos incompletos o inconsistentes.
- Rate limits o bloqueos temporales.
- Clasificaciones incorrectas si la IA recibe poco contexto.
- Duplicados dificiles cuando cambian nombre y direccion al mismo tiempo.

## Mejoras futuras

- Notificaciones Slack/email.
- Panel de aprobacion.
- Historial completo de cambios.
- Agente IA que responda preguntas sobre los bares cargados.
- Export CSV/JSON.
