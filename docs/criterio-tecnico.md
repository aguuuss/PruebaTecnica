# Criterio tecnico y defensa de la solucion

Este documento resume como el proyecto cubre los puntos principales de la prueba tecnica y como explicarlos en una demo.

## Scraping no agresivo

El sistema obtiene bares/restaurantes desde una fuente publica: Tucuman Turismo.

La obtencion de datos no es agresiva porque:

- Hace una unica request por ejecucion del importador.
- Usa timeout para evitar procesos colgados.
- Usa un user-agent identificable.
- No hace crawling masivo ni llamadas en paralelo.
- Si la fuente falla o cambia su HTML, el flujo no se rompe: usa un dataset mock de respaldo.

El scraping solo se encarga de obtener datos crudos como nombre, direccion, localidad, contacto, horarios y servicios.

## CRUD

El sistema permite administrar los datos obtenidos:

- Listar lugares cargados.
- Crear lugares manualmente.
- Editar datos principales.
- Desactivar registros sin borrarlos fisicamente.

La desactivacion logica permite conservar trazabilidad y evita perder informacion historica.

## Automatizacion

La automatizacion principal esta encapsulada en este comando:

```bash
python -m app.jobs.import_bars
```

Cada ejecucion realiza el flujo completo:

```text
Scraping
→ parseo
→ normalizacion
→ enriquecimiento con IA o fallback
→ deteccion de duplicados
→ guardado/actualizacion
→ registro de logs
```

Este comando puede ejecutarse:

- Manualmente.
- Con cron en un VPS.
- Con Windows Task Scheduler.
- Desde n8n mediante SSH o HTTP.

El archivo `deploy/n8n-flow-notes.md` describe como conectarlo con n8n.

## Uso de IA

La IA no es necesaria para hacer scraping. El scraping funciona sin API key porque solo lee una web publica.

La IA se aplica despues de obtener los datos, durante el procesamiento previo al guardado.

El servicio de IA esta en:

```text
backend/app/services/ai.py
```

Y se usa desde:

```text
backend/app/services/importer.py
```

Aplicaciones actuales:

- Clasificar el lugar: bar, restaurante, cafe, pizzeria, heladeria, regional u otro.
- Generar una descripcion breve del lugar.
- Dejar preparada la base para mejorar deteccion de duplicados ambiguos.

Si existe `OPENAI_API_KEY`, el sistema usa OpenAI. Si no existe o la llamada falla, usa un fallback local basado en reglas simples.

Esto permite que la demo funcione siempre, incluso sin credenciales externas.

## Fallback sin API key

El fallback local evita que el flujo dependa 100% de OpenAI.

Ejemplos:

- Si el nombre o servicios contienen "pizza", clasifica como `pizzeria`.
- Si contienen "cafe", clasifica como `cafe`.
- Si contienen "helado", clasifica como `heladeria`.
- Si no hay una senal clara, clasifica como `bar`.

De esta forma, el flujo mantiene continuidad:

```text
Scraping real: si
OpenAI real: solo si hay API key
Fallback local: si
```

Frase sugerida para la demo:

> La integracion con OpenAI es opcional por variable de entorno. Si no hay API key o falla la API, el flujo no se rompe: usa un fallback local y registra igual la importacion.

## Deteccion de duplicados

El sistema evita duplicados con dos estrategias:

1. Normalizacion:
   - Convierte texto a minusculas.
   - Quita acentos.
   - Quita signos.
   - Elimina palabras comunes como "bar", "restaurante" o "tucuman".

2. Similitud:
   - Compara nombre y direccion normalizados.
   - Si la similitud supera el umbral definido, actualiza el registro existente en vez de crear uno nuevo.

Ejemplo:

```text
Bar Irlanda Tucuman
Irlanda Bar
```

Ambos pueden terminar normalizados como una misma entidad si comparten senales suficientes, especialmente direccion.

## Logs

Cada importacion genera un registro con:

- Estado.
- Cantidad de items encontrados.
- Cantidad de registros creados.
- Cantidad de registros actualizados.
- Cantidad de duplicados detectados.
- Error o advertencia si corresponde.
- Fecha de inicio y fin.

Esto permite auditar el proceso y mostrar en el dashboard que la automatizacion efectivamente corrio.

## Escalabilidad

Para escalar el sistema:

- Reemplazar SQLite por PostgreSQL o Supabase.
- Agregar multiples fuentes de datos.
- Mover la importacion a una cola de trabajos.
- Agregar autenticacion al endpoint de importacion.
- Guardar historial de cambios por campo.
- Usar embeddings para deduplicacion semantica.
- Agregar aprobacion manual antes de publicar nuevos registros.

## Problemas posibles

- La fuente puede cambiar su HTML.
- Algunos datos pueden venir incompletos.
- Puede haber duplicados dificiles si cambia nombre y direccion.
- La IA puede clasificar mal si el contexto es pobre.
- La API de OpenAI puede fallar o no estar configurada.

Por eso el sistema tiene fallback, logs y una UI donde los datos se pueden corregir manualmente.
