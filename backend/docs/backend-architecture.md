# Arquitectura Backend — Token Optimizer App

## 1. Resumen general

Servicio backend en **FastAPI** responsable de:

1. Tokenizar texto en español e inglés (`tiktoken`, encoder `o200k_base`).
2. Traducir de forma **contextual y natural** (no literal) entre ES↔EN, usando dos motores intercambiables: **Ollama local** o **DeepL API**.
3. Generar una versión **"Spanglish"** que combine palabras de ambos idiomas priorizando las de menor conteo de tokens, sin romper la comprensión del texto.
4. Devolver al frontend las 3 variantes del texto (original, traducido natural, spanglish) junto con su conteo de tokens respectivo.
5. Ejecutar el caso de estudio de clasificación de reseñas de tiendas de apps (crash reports), con soporte de ingesta desde Excel (archivo único o carpeta) y cálculo de proyección de costos a escala.

## 2. Stack tecnológico

| Capa                           | Tecnología                                  |
| ------------------------------ | ------------------------------------------- |
| Framework API                  | FastAPI                                     |
| Tokenización                   | `tiktoken` (encoder `o200k_base`)           |
| Traducción remota              | DeepL API (API key aportada por el usuario) |
| Traducción local               | Ollama (modelo local, sin costo por token)  |
| Traducción auxiliar / fallback | `deep_translator`                           |
| Ingesta de datos               | `pandas`, `openpyxl`, `pathlib`             |
| Validación de datos            | Pydantic v2                                 |

## 3. Endpoints principales

### 3.1 `POST /api/tokenize`

Cuenta tokens de un texto crudo, sin traducir.

**Request**

```json
{ "text": "string", "encoding": "o200k_base" }
```

**Response**

```json
{ "text": "string", "token_count": 0, "detected_language": "es" }
```

### 3.2 `POST /api/analyze`

Endpoint principal. Recibe un texto y devuelve las 3 variantes (original / traducido natural / spanglish) con tokens de cada una, más — cuando aplica al caso de estudio — la clasificación estructurada del LLM.

**Request**

```json
{
  "text": "La aplicación se cierra inesperadamente cada vez que intento subir una foto de perfil desde la galería de mi teléfono.",
  "engine": "ollama | deepl",
  "classify": true
}
```

**Response**

```json
{
  "original": { "text": "...", "language": "es", "token_count": 27 },
  "translated": { "text": "...", "language": "en", "token_count": 19 },
  "spanglish": { "text": "...", "token_count": 15 },
  "classification": {
    "error_type": "crash",
    "component": "profile_picture_upload"
  },
  "engine_used": "ollama"
}
```

### 3.3 `POST /api/translate`

Servicio interno/reutilizable de traducción pura (sin tokenizar ni clasificar). Recibe `engine` (`ollama` o `deepl`) y hace fallback automático al otro motor si el primero falla o no está disponible.

### 3.4 `GET /api/config/status`

Verifica disponibilidad de motores: si Ollama está corriendo localmente y si hay una API key de DeepL válida configurada (la key vive en el navegador vía `localStorage`, el backend solo la recibe por request cuando se necesita, nunca la persiste en servidor).

### 3.5 `POST /api/batch/upload`

Ingesta de un único archivo `.xlsx` con reseñas. Aplica `/api/analyze` fila por fila (con o sin traducción, según flag).

### 3.6 `POST /api/batch/folder`

Ingesta por lote: recibe una ruta local de carpeta, consolida todos los `.xlsx` encontrados con `pandas`/`pathlib`, y procesa cada fila.

**Request (POST /api/batch/upload - Form Data)**

- `file`: Archivo Excel (.xlsx)
- `optent_tokens`: boolean (por defecto `true`)
- `engine`: `"ollama" | "deepl"` (por defecto `"ollama"`)

**Request (POST /api/batch/folder - JSON Body)**

```json
{
  "folder_path": "/ruta/a/la/carpeta",
  "optent_tokens": true,
  "engine": "ollama"
}
```

### 3.7 `POST /api/analyze/projection`

Calcula proyección económica a escala.

**Request**

```json
{
  "tokens_original": 27,
  "tokens_translated": 19,
  "reviews_per_day": 10000,
  "cost_per_million_tokens_usd": 2.5,
  "days": 30
}
```

**Response**

```json
{
  "daily_token_diff": 80000,
  "monthly_token_diff": 2400000,
  "monthly_savings_usd": 6.0
}
```

## 4. Modelos de datos (Pydantic) — esquema base

```python
class AnalyzeRequest(BaseModel):
    text: str
    engine: Literal["ollama", "deepl"] = "ollama"
    classify: bool = False

class TokenVariant(BaseModel):
    text: str
    language: str
    token_count: int

class AnalyzeResponse(BaseModel):
    original: TokenVariant
    translated: TokenVariant
    spanglish: TokenVariant
    classification: Classification | None = None
    engine_used: str
```

## 5. Motores de traducción

- **Ollama (local), modelo `2:7b`:** primera opción por defecto, sin costo de API. Se le pide explícitamente que la traducción sea natural y conserve el contexto (no literal), vía prompt de sistema. Este mismo modelo recibe un **prompt-tuning específico para spanglish**: un system prompt dedicado (no el mismo que el de traducción natural) que le instruye explícitamente a mezclar palabras de ambos idiomas priorizando la de menor longitud/tokens por concepto, manteniendo la oración gramaticalmente coherente.
- **DeepL (remoto):** requiere API key introducida por el usuario en el frontend; el backend la recibe por header/body en cada llamada, nunca la guarda en disco/base de datos.
- **Spanglish — enfoque híbrido (LLM + diccionario):**
  1. **Diccionario base (`spanglish_dict.json`):** archivo estático con pares de palabras/expresiones donde una es notablemente más larga en tokens que su equivalente en el otro idioma (ej. `"desafortunadamente" → "unfortunately"` si conviene, o casos inversos donde la palabra en inglés es más larga). Se usa como paso de sustitución rápida y determinista, sin costo de LLM.
  2. **Post-procesamiento con Ollama (prompt-tuning):** sobre el resultado del diccionario, el modelo ajusta la frase para que siga siendo natural y legible, resolviendo concordancia y orden de palabras.
  3. Este enfoque combina velocidad/consistencia (diccionario) con calidad lingüística (LLM), y permite ampliar el diccionario con el tiempo sin reentrenar nada.

### 5.1 Estructura sugerida de `spanglish_dict.json`

```json
{
  "es_to_en": {
    "desafortunadamente": "unfortunately",
    "inmediatamente": "right now"
  },
  "en_to_es": {
    "nevertheless": "aun así",
    "approximately": "como"
  }
}
```

Este archivo vive en el backend (ej. `app/data/spanglish_dict.json`), se carga en memoria al iniciar el servicio y se consulta antes de invocar al LLM para el paso de spanglish.

## 6. Épicas e Historias de Usuario (Backend)

### Épica A — Tokenización y Traducción Core

**HU-001 — Conteo de tokens de un texto**
Como usuario quiero enviar un texto y obtener su conteo exacto de tokens (`o200k_base`) para saber cuánto me cuesta ese prompt.

- Criterios: detecta idioma; usa `tiktoken`; responde en <300ms para textos cortos.

**HU-002 — Traducción contextual natural**
Como usuario quiero que el texto se traduzca de forma natural (no literal) manteniendo el contexto, para no perder matices al cambiar de idioma.

- Criterios: prompt de traducción explícitamente pide fluidez natural, no traducción palabra por palabra; funciona ES→EN y EN→ES.

**HU-003 — Generación de versión Spanglish**
Como usuario quiero una tercera opción que mezcle ES/EN priorizando palabras más cortas en tokens, para minimizar el costo del prompt sin perder comprensión.

- Criterios: primero se aplica el diccionario `spanglish_dict.json` para sustituciones directas; luego Ollama (con su prompt-tuning específico) ajusta la coherencia gramatical de la frase resultante; la salida sigue siendo legible; se listan tokens ahorrados vs. original y vs. traducido.

**HU-003b — Diccionario de sustituciones Spanglish**
Como desarrollador quiero mantener un archivo `spanglish_dict.json` con pares de palabras ES↔EN donde una es más costosa en tokens que la otra, para acelerar y abaratar la generación de la versión spanglish sin depender únicamente del LLM.

- Criterios: el archivo se carga en memoria al iniciar el servicio; es fácilmente editable/ampliable sin tocar código; se aplica antes del paso de LLM.

**HU-004 — Selección de motor de traducción**
Como usuario quiero elegir entre Ollama local o DeepL para traducir, con fallback automático si uno falla.

- Criterios: si `engine=ollama` falla (no corriendo), intenta DeepL automáticamente y lo indica en `engine_used`.

**HU-005 — Endpoint unificado `/api/analyze`**
Como frontend quiero un único endpoint que devuelva las 3 variantes y sus tokens en una sola llamada, para simplificar la UI.

### Épica B — Caso de Estudio: Feedback de App Stores

**HU-006 — Clasificación estructurada del feedback**
Como analista quiero que `/api/analyze` devuelva un JSON con `error_type` y `component` extraídos por el LLM, para automatizar el triage de fallas.

**HU-007 — Proyección de tokens a escala (10,000 reseñas/día)**
Como analista quiero calcular la diferencia de tokens entre texto original y traducido multiplicada por 10,000 reseñas/día y por 30 días, para dimensionar el volumen de procesamiento.

**HU-008 — Cálculo de ahorro económico mensual**
Como analista quiero calcular el ahorro en USD mensual asumiendo $2.50 por millón de tokens, comparando el flujo con y sin traducción previa, para justificar el arbitraje de traducción como optimización de costos.

### Épica C — Ingesta de Datos desde Excel

**HU-012 — Ingesta flexible de datos y optimización opcional de tokens** _(provista por el usuario)_
Como Analista de Datos / Desarrollador quiero un sistema de ingesta que procese un Excel individual o una carpeta completa de Excels con reseñas, aplicando opcionalmente el paso de traducción/optimización vía `/api/analyze`, para extraer el problema técnico principal con flexibilidad de fuente y control de costos.

- **Criterio 1 — Ingesta flexible:** Modo A (archivo único `.xlsx`) y Modo B (carpeta local, consolidando todos los `.xlsx`); debe validar que la columna de reseña se detecte correctamente en ambos modos.
- **Criterio 2 — Pipeline opcional:** bandera `optent_tokens: True/False`; si es `True` traduce antes del LLM principal (`o200k_base`); si es `False` procesa el texto original directo.
- **Criterio 3 — Impacto económico y salida estructurada:** calcula volumen total de tokens y diferencia de costo ($2.50/millón) para 10,000 reseñas/día comparando directo vs. optimizado; exporta resultados en JSON/Excel limpio (ej. `{"error_type": "crash", "component": "profile_picture_upload"}`).
- Story Points: 3.

**HU-013 — Exportación de resultados batch**
Como analista quiero exportar los resultados clasificados de un lote (archivo o carpeta) a un Excel de salida, para compartir el análisis con el equipo de producto.

## 7. Notas técnicas / dependencias sugeridas

```
fastapi
uvicorn
tiktoken
pandas
openpyxl
pathlib (stdlib)
deep-translator
pydantic
httpx  # para llamar a Ollama local (REST) y a la API de DeepL
faker
python-multipart
```

## 8. Decisiones confirmadas

- **Modelo Ollama:** `2:7b`.
- **Sin autenticación:** la app no maneja login/usuarios; todos los endpoints son de acceso abierto (uso local/monousuario).
- **Sin persistencia (por ahora):** no hay base de datos; todo el procesamiento es _stateless_ por request. El historial de análisis, si se necesita, vive únicamente en el estado del frontend/sesión del navegador.
