# Token Bender - Optimizador de Tokens para LLMs

Token Bender es una aplicacion web diseñada para optimizar los costos de procesamiento de texto con Modelos de Lenguaje Grande (LLMs). Se enfoca en analizar y reducir el consumo de tokens mediante la traduccion de reseñas de aplicaciones del español al ingles (ya que el ingles utiliza significativamente menos tokens para representar el mismo significado semantico en tokenizadores como tiktoken).

El sistema cuenta con un frontend interactivo en React y un backend robusto construido en FastAPI.

## Caracteristicas Principales

- Analisis de Tokens: Cuenta de forma precisa la cantidad de tokens de un texto utilizando la codificacion o200k_base (a traves de tiktoken).
- Traduccion Optimizada: Traduce reseñas entre español e ingles utilizando motores como DeepL o traductores alternativos.
- Analisis de Spanglish: Permite generar versiones hibridas para de ahorro de tokens y analisis.
- Clasificacion de Reseñas: Clasifica las reseñas en categorias de error (crash, bug, performance, ui, network, feature_request) e identifica el componente afectado (login, payment, settings, etc.) utilizando modelos locales en Ollama o un clasificador de respaldo basado en reglas.
- Ingesta por Lote (Excel): Permite la carga de archivos Excel con multiples reseñas para calcular el ahorro economico consolidado y procesar clasificaciones de forma masiva.
- Calculadora de Proyeccion: Permite simular y proyectar los ahorros diarios y mensuales basandose en volumenes personalizados de reseñas y costo por millon de tokens.

## Estructura del Proyecto

El proyecto esta organizado en las siguientes carpetas y archivos clave:

- backend/: Contiene el servidor de la API desarrollado en FastAPI.
  - app/main.py: Punto de entrada de la aplicacion.
  - app/routers/: Define los endpoints de la API (tokenize, analyze, translate, config_router, batch).
  - app/services/: Logica de negocio para tokenizacion, traduccion, clasificacion y generacion de Spanglish.
  - app/models/: Esquemas de validacion de datos con Pydantic.
  - requirements.txt: Lista de dependencias del backend.
- frontend/: Contiene la interfaz de usuario en React, TypeScript y Vite.
  - src/App.tsx: Layout principal y navegacion.
  - src/components/: Componentes de la interfaz de usuario (MainWindow, ConfigPanel, ExcelIngest, ProjectionPanel).
  - src/store/: Manejo de estado global con Zustand.
- start.sh: Script en Bash para iniciar de forma concurrente el frontend y el backend en entornos basados en Unix.
- requirements.txt: Archivo de dependencias Python en la raiz del proyecto para facilitar la instalacion.

## Requisitos Previos

- Python 3.10 o superior
- Node.js (v18 o superior) y npm
- Ollama (opcional, necesario para ejecucion de clasificacion local con LLMs)

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
- POST /api/batch/folder: Analiza todos los archivos Excel dentro de una ruta de carpeta local especificada.
- POST /api/analyze/projection: Calcula la proyeccion de ahorro financiero y de tokens.

## Licencia

Este proyecto esta bajo una licencia libre para desarrollo y aprendizaje.
