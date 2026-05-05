# n8n flow sugerido

Este repo deja la automatizacion real en un comando idempotente. n8n puede actuar como orquestador sin duplicar la logica.

## Flujo recomendado

1. Cron Trigger: cada dia a la madrugada.
2. SSH: conectarse al VPS.
3. Execute Command:

```bash
cd /ruta/al/proyecto && docker compose exec -T backend python -m app.jobs.import_bars
```

4. IF: revisar si el output contiene `error`.
5. Slack/Email:
   - OK: cantidad de nuevos, actualizados y duplicados.
   - Error: mensaje del log.

## Alternativa por HTTP

Tambien se puede llamar:

```bash
curl -X POST https://api.tudominio.com/imports/run
```

Para produccion real conviene proteger ese endpoint con un token o dejarlo solo accesible por VPN/red interna.
