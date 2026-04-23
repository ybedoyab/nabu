# Nabu

Asistente inteligente para descubrimiento, comparación y chat sobre artículos de investigación.  
MVP orientado a consultas por sesión usando `arXiv` y `Google Scholar` sin mantener un dataset histórico permanente.

## Objetivo

- Encontrar artículos relevantes más rápido.
- Resumir aportes clave de forma accionable.
- Comparar trabajos relacionados.
- Responder preguntas con trazabilidad a fuentes.

## Arquitectura

- `frontend/`: UI React.
- `backend/`: API principal + orquestación + casos de uso.
- `data/`: ingesta/normalización por sesión y utilidades ETL.
- `ai/`: servicios de IA y flujo conversacional (modularizado por capas).

Flujo general:
1. Usuario envía `query`.
2. Ingesta acotada por límites (`arxiv`, `scholar`).
3. Normalización + deduplicación + `session_id` con TTL.
4. Recomendaciones, resúmenes, comparación y chat sobre ese corpus.

## Estructura de Proyecto

```text
.
├── requirements.txt
├── settings.py
├── docker-compose.yml
├── deploy.ps1
├── backend/
│   ├── Dockerfile
│   ├── main.py
│   └── src/
├── data/
│   ├── Dockerfile
│   ├── api.py
│   ├── src/
│   └── webscraping/
└── ai/
    ├── Dockerfile
    ├── main.py
    └── src/
```

## Capa AI (modular)

`ai/src` está organizado por capas:
- `adapters/inbound`: disparadores de entrada (CLI).
- `adapters/outbound`: clientes/proveedores externos.
- `application/services`: orquestación de casos de uso.
- `domain`: entidades/reglas núcleo.
- `ports`: contratos para integraciones futuras.
- `infrastructure`: configuración runtime.

## Capa Data y Webscraping

Base de fuentes en `data/webscraping`:
- `arxiv/`
  - `raw/`
  - `normalized/`
  - `logs/`
- `google_scholar/`
  - `raw/`
  - `normalized/`
  - `logs/`

Convención:
- separar crudo vs normalizado,
- guardar trazas en `logs/`,
- operar por sesión (on-demand) en el MVP.

## Configuración

### Variables sensibles en `.env`

Solo secretos:
- `OPENAI_API_KEY`

El resto de parámetros vive en `settings.py` (modelo, temperatura, límites, etc.).

### Dependencias

Unificadas en:
- `requirements.txt` (raíz)

## Ejecución local rápida

### Flujo recomendado (único comando)

```powershell
.\deploy.ps1 --local
```

`deploy.ps1` está preparado para primera ejecución y ejecuciones posteriores:

- Verifica prerequisitos (`python/py`, `npm`; usa `winget` para instalar si faltan).
- Crea `.env` automáticamente desde `env.example` si no existe. (usar el compartido como material suplementario en el forms)
- Crea `.venv` si no existe.
- Instala/actualiza dependencias Python desde `requirements.txt` cuando cambian.
- Instala/actualiza dependencias frontend (`npm install`) cuando cambia `package-lock.json`.
- Libera automáticamente puertos ocupados `8000`, `8081`, `3000`.
- Levanta `backend`, `data` y `frontend`, valida readiness y deja logs en streaming.

### Modo Docker

```powershell
.\deploy.ps1 --docker
```

## Endpoints y URLs locales

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Backend docs: `http://localhost:8000/docs`
- Data API: `http://localhost:8081`
- Data health: `http://localhost:8081/health`

## Notas de primera ejecución

- Si `winget` instala Python o Node.js por primera vez y no aparecen en PATH inmediatamente, reinicia la terminal y vuelve a ejecutar `.\deploy.ps1 --local`.
- Si `.env` fue creado automáticamente, configura `OPENAI_API_KEY` para habilitar todas las funciones de IA.

## Testing

### Python (backend/ai/data)

```bash
python -m pytest
```

### Frontend

```bash
cd frontend
npm run test:coverage
```

## Contrato base de sesión (`/api/v1/session/fetch`)

Entrada:

```json
{
  "query": "efficient transformers long context",
  "limits": { "arxiv": 15, "scholar": 10 },
  "locale": "es"
}
```

Salida:
- `session_id`
- `ttl_seconds`, `expires_at`
- `articles[]` normalizados
- `stats` (`merged_unique`, `duplicates_removed`)
- `errors_by_source` en caso parcial

## Estado de despliegue

- `deploy.ps1 --local`: operativo para desarrollo local.
- Flujo cloud se ajustará en una etapa posterior.
