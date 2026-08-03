
# Token Bender - Optimizador de Tokens para LLMs

Token Bender es una aplicacion web diseñada para optimizar los costos de procesamiento de texto con Modelos de Lenguaje Grande (LLMs). Se enfoca en analizar y reducir el consumo de tokens mediante la traduccion de reseñas de aplicaciones del español al ingles (ya que el ingles utiliza significativamente menos tokens para representar el mismo significado semantico en tokenizadores como tiktoken).

El sistema cuenta con un frontend interactivo en React y un backend robusto construido en FastAPI.

## Caracteristicas Principales

- Analisis de Tokens: Cuenta de forma precisa la cantidad de tokens de un texto utilizando la codificacion o200k_base (a traves de tiktoken).
- Traduccion Optimizada: Traduce reseñas entre español e ingles utilizando el motor local CTranslate2 / MarianMT (CPU).
- Analisis de Spanglish: Permite generar versiones hibridas para de ahorro de tokens y analisis.
- Clasificacion de Reseñas: Clasifica las reseñas en categorias de error (crash, bug, performance, ui, network, feature_request) e identifica el componente afectado (login, payment, settings, etc.) mediante un clasificador basado en reglas.
- Ingesta por Lote (Excel): Permite la carga de archivos Excel con multiples reseñas para calcular el ahorro economico consolidado y procesar clasificaciones de forma masiva.
- Proyeccion en Resultados: Muestra el ahorro economico estimado (diario, semanal, mensual) dentro de los resultados del proceso batch.

## Estructura del Proyecto

El proyecto esta organizado en las siguientes carpetas y archivos clave:

- backend/: Contiene el servidor de la API desarrollado en FastAPI.
  - app/main.py: Punto de entrada de la aplicacion.
  - app/routers/: Define los endpoints de la API (tokenize, analyze, translate, config_router, batch).
  - app/services/: Logica de negocio para tokenizacion, traduccion, clasificacion y generacion de Spanglish.
  - app/models/: Esquemas de validacion de datos con Pydantic.
  - requirements.txt: Lista de dependencias del backend.
- frontend/: Contiene la interfaz de usuario en React, TypeScript y Vite.
  - src/App.tsx: Layout principal (solo ingesta Excel + configuración en modal).
  - src/components/: Componentes de la interfaz de usuario (ExcelIngest, ConfigPanel, ConsoleWindow, TitleBar, Button).
- start.sh: Script en Bash para iniciar de forma concurrente el frontend y el backend en entornos basados en Unix.
- requirements.txt: Archivo de dependencias Python en la raiz del proyecto para facilitar la instalacion.

## Requisitos Previos

- Python 3.10 o superior
- Node.js (v18 o superior) y npm

## Instalacion y Configuracion

### 1. Clonar el repositorio y acceder
Navegue al directorio raiz del proyecto:
cd token-bender

### 2. Configurar el Backend
1. Ingrese a la carpeta backend:
   cd backend
2. Cree un entorno virtual de Python:
   python -m venv venv
3. Active el entorno virtual:
   - En Windows:
     venv\Scripts\activate
   - En Linux/macOS:
     source venv/bin/activate
4. Instale las dependencias necesarias:
   pip install -r requirements.txt
5. Inicie el servidor de desarrollo:
   uvicorn app.main:app --reload --port 8000

El backend estara disponible en: http://localhost:8000

### 3. Configurar el Frontend
1. Ingrese a la carpeta frontend:
   cd ../frontend
2. Instale las dependencias de Node:
   npm install
3. Inicie el servidor de desarrollo de Vite:
   npm run dev

El frontend estara disponible en: http://localhost:5173

### 4. Ejecucion Automatizada (Unix/Git Bash)
Si esta utilizando un sistema Unix o Git Bash en Windows, puede utilizar el script de arranque provisto:
./start.sh

## Uso de la API (Endpoints del Backend)

El backend expone la documentacion interactiva en http://localhost:8000/docs. Los principales endpoints son:

- POST /api/tokenize: Recibe un texto y devuelve el conteo de tokens y el idioma detectado.
- POST /api/analyze: Traduce el texto, cuenta tokens antes y despues de la traduccion, genera Spanglish y realiza clasificacion.
- POST /api/batch/upload: Procesa un archivo Excel con reseñas enviadas como multipart/form-data.
- POST /api/batch/folder: Procesa todos los archivos Excel de una carpeta seleccionada (subidos como archivos múltiples).

## Licencia

Este proyecto esta bajo una licencia libre para desarrollo y aprendizaje.
=======
# Token Optimizer

Optimización de tokens para LLMs mediante traducción contextual y generación de Spanglish. Enfocado en el análisis de reseñas de app stores en español.

## Propuesta de valor

Traducir reseñas en español a inglés (o generar Spanglish) reduce significativamente el conteo de tokens. Esto se traduce en ahorros económicos directos al usar APIs de LLMs que cobran por token. El proyecto incluye un analizador de impacto económico que proyecta el ahorro a escala (10,000 reseñas/día).

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3, FastAPI, Uvicorn |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS 4 |
| Cliente HTTP | Axios (con proxy Vite) |
| Tokenización | `tiktoken` (encoder `o200k_base`) |
| Traducción | CTranslate2 + MarianMT (local, CPU) |
| Clasificación | Fallback heurístico por palabras clave |
| Excel | pandas / openpyxl (backend) · `xlsx` SheetJS (frontend) |
| Tests | pytest + pytest-asyncio + httpx |

## Estructura del proyecto

```
clase2/
├── backend/
│   ├── app/
│   │   ├── main.py              # Punto de entrada FastAPI + CORS
│   │   ├── config.py            # Constantes (encoding)
│   │   ├── models/
│   │   │   ├── analyze.py       # Schemas: tokenize, analyze, translate
│   │   │   ├── batch.py         # Schemas: batch results, summary
│   │   │   ├── config.py        # Schemas: config status
│   │   │   └── schemas.py       # Re-exports (compatibilidad)
│   │   ├── services/
│   │   │   ├── tokenizer.py     # tiktoken + langdetect
│   │   │   ├── translator.py    # CTranslate2
│   │   │   ├── spanglish.py     # Diccionario de sustituciones
│   │   │   ├── classifier.py    # Clasificación de reseñas (heurística)
│   │   │   ├── ctranslate_service.py # Motor CTranslate2 / MarianMT
│   │   │   ├── batch/           # Procesamiento batch (io, columnas, economía, orquestación)
│   │   │   └── clustering/      # Intenciones (1-5 estrellas) y agrupamiento semántico
│   │   ├── routers/
│   │   │   ├── tokenize.py      # POST /api/tokenize
│   │   │   ├── analyze.py       # POST /api/analyze (endpoint principal)
│   │   │   ├── translate.py     # POST /api/translate
│   │   │   ├── config_router.py # GET /api/config/status
│   │   │   └── batch.py         # POST /api/batch/upload, /batch/folder, /batch/start, /batch/progress
│   │   └── data/
│   │       └── spanglish_dict.json  # ~500 pares ES↔EN
│   ├── tests/                   # Tests unitarios y de integración
│   ├── generate_excel.py        # Generador de Excel con reseñas sintéticas
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ExcelIngest.tsx    # Orquestador principal (composición)
│   │   │   ├── upload/            # Tabs, zonas drag&drop (archivo y carpeta)
│   │   │   ├── results/           # KPI grid, costos, ratings, tabla de resultados
│   │   │   ├── ConfigPanel.tsx    # Modal de configuración (estado CTranslate2)
│   │   │   ├── ConsoleWindow.tsx  # Consola de proceso
│   │   │   └── Button.tsx         # Botón moderno
│   │   ├── hooks/useBatchProcessing.ts  # Estado y lógica del procesamiento batch
│   │   ├── utils/                # Formateo y export a Excel
│   │   ├── api/client.ts        # Axios (proxy automático a backend)
│   │   └── types/index.ts       # Interfaces TypeScript
│   ├── vite.config.ts           # Proxy /api → localhost:8000, Tailwind plugin
│   └── package.json
├── archivos_ejemplo/
│   ├── excel_generator.py       # Generador de Excel (50k reseñas de ejemplo)
│   └── resenas_productos_50k.xlsx
├── start.sh                     # Script para arrancar backend + frontend
└── README.md
```

## Endpoints de la API

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/api/tokenize` | Tokeniza texto y detecta idioma |
| `POST` | `/api/analyze` | **Principal.** Tokeniza, traduce, genera Spanglish y clasifica |
| `POST` | `/api/translate` | Traducción pura con CTranslate2 |
| `GET` | `/api/config/status` | Estado del motor CTranslate2 |
| `POST` | `/api/batch/upload` | Procesa Excel individual (clasifica por fila + proyección económica) |
| `POST` | `/api/batch/folder` | Procesa todos los `.xlsx`/`.csv` de una carpeta (subida múltiple) |
| `POST` | `/api/batch/start` | Inicia proceso batch en background (upload) |
| `GET` | `/api/batch/progress/{task_id}` | Consulta el progreso de un batch |

### Flujo del endpoint principal (`POST /api/analyze`)

```
Texto original
    │
    ├─ 1. Detectar idioma (langdetect)
    ├─ 2. Tokenizar (tiktoken o200k_base)
    ├─ 3. Traducir al idioma opuesto (CTranslate2 / MarianMT)
    ├─ 4. Generar Spanglish (diccionario de sustituciones)
    └─ 5. Clasificar (heurística por palabras clave)
    │
    └─ Devuelve: original, translated, spanglish + conteo de tokens + clasificación
```

### Clasificación de reseñas

El clasificador extrae dos campos de cada reseña:

- **error_type**: `crash`, `bug`, `performance`, `ui`, `network`, `feature_request`
- **component**: `login`, `signup`, `profile_picture_upload`, `gallery`, `camera`, `chat`, `payment`, `checkout`, `notifications`, `settings`, `video_player`, `audio_player`, `file_download`, `search`, `map`, entre otros.

## Requisitos

- Python 3.11+ (con las librerías: `fastapi`, `uvicorn`, `tiktoken`, `pandas`, `openpyxl`, `pydantic`, `httpx`, `langdetect`, `deep-translator`, `faker`, `python-multipart`, `ctranslate2`, `transformers`, `sentencepiece`, `torch`, `sacremoses`)
- Node.js 20+

## Inicio rápido

```bash
# 1. Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 2. Frontend (otra terminal)
cd frontend
npm install
npm run dev -- --port 5173

# 3. Abrir http://localhost:5173
```

O usar el script combinado:

```bash
./start.sh
```

## Generar datos de prueba

```bash
cd backend
source venv/bin/activate
python generate_excel.py -n 100 -o resenas.xlsx
```

## Tests

```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v
```

## Componentes del frontend

| Panel | Ubicación | Función |
|-------|---------|---------|
| **ExcelIngest** | Principal | Subir `.xlsx`, preview local, toggle de optimización, tabla de resultados clasificados, proyección económica, exportación a Excel |
| **ConfigPanel** | Modal (botón Configuración arriba a la derecha) | Estado del motor CTranslate2 |

## Conexión frontend-backend

Durante desarrollo, Vite actúa como proxy: toda petición a `/api/*` desde el frontend se redirige automáticamente a `http://localhost:8000/api/*`. No se necesita configuración adicional de CORS.

## Licencia

MIT

