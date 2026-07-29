# Blueprint de Optimizacion: Categorizacion Masiva de Resenas

**Objetivo:** Procesar 50,000 resenas en <30 segundos minimizando tokens de LLM.

## Estrategia de 3 Pilares

### 1. Agrupacion por Lotes (Batching)
100 resenas por prompt estructurado (JSON comprimido).
50,000 llamadas -> 500 solicitudes totales.

### 2. Concurrencia Controlada
`asyncio.Semaphore` + `asyncio.gather` para saturar el canal sin exceder
limites de tasa del proveedor.

### 3. Reduccion de Tokens
- **Entrada:** Categorias e instrucciones se envian una vez por lote.
- **Salida:** Solo IDs y codigos de categoria: `[{"id":1,"c":2}]`

## Implementacion Actual en Token Bender

| Principio | Implementacion |
|-----------|---------------|
| Batching | Argos Translate `batch_translate()` agrupa textos unicos |
| Concurrencia | `asyncio.gather` con `Semaphore(5)` por grupos de producto |
| Min tokens | Clasificador por keywords (sin LLM), cache de textos unicos |
| Output minimo | `Classification` con solo `error_type` + `component` |

## Diferencia Clave con el Blueprint Original

El blueprint asume uso de API externa (OpenAI) con rate limits.
Token Bender usa **Argos Translate** (local, sin rate limits) +
**clasificador por keywords** (instantaneo), por lo que el cuello
de botella no son las llamadas HTTP sino la inferencia del modelo
local.

Las optimizaciones aplicadas del blueprint:
- Cache de traduccion, clasificacion y token counts por texto unico
- Batching por grupo de producto
- Procesamiento paralelo de grupos
