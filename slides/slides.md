---
theme: default
title: Token Bender
info: |
  Optimizador de tokens para LLMs mediante traducción contextual y análisis de reseñas.
class: text-left
drawings:
  persist: false
transition: slide-left
mdc: true
---

# Token Bender

Optimización de tokens para LLMs mediante traducción contextual

<div class="pt-12">
  <span class="tb-chip">📊 Análisis de reseñas</span>
  <span class="tb-chip">💰 Ahorro económico</span>
  <span class="tb-chip">🚀 Traducción local</span>
</div>

<div class="abs-br m-6 flex gap-2 text-dim text-sm">
  React 19 · FastAPI · CTranslate2
</div>

---
layout: two-cols
---

# El problema

Los LLMs cobran por **token**.

- Traducir reseñas en español a inglés reduce significativamente los tokens
- El inglés usa menos tokens para el mismo significado (encoder `o200k_base`)
- A escala (10,000 reseñas/día) el ahorro es económico real

::right::

<br>

<div class="tb-card">
  <div class="text-5xl font-bold text-red">27</div>
  <div class="text-sm text-dim mt-1">tokens (ES)</div>

  <div class="text-5xl font-bold text-green mt-6">19</div>
  <div class="text-sm text-dim mt-1">tokens (EN)</div>

  <div class="text-sm text-dim mt-6">≈ 30% menos por reseña</div>
</div>

---
layout: two-cols
---

# La solución

**Token Bender** es una app web que:

- Traduce reseñas **ES → EN** con CTranslate2 / MarianMT (100% local, CPU)
- Cuenta tokens con `tiktoken`
- Agrupa reseñas en 5 intenciones por producto
- Calcula el **ahorro económico** proyectado

::right::

<br>

<div class="tb-card">
  <div class="font-bold text-sm text-dim uppercase tracking-wide">Flujo</div>
  <div class="mt-4 space-y-2 text-sm text-muted">
    <div>1. Detectar idioma</div>
    <div>2. Traducir (ES → EN)</div>
    <div>3. Agrupar por intención ⭐</div>
    <div>4. Calcular ahorro</div>
    <div>5. Exportar a Excel</div>
  </div>
</div>

---
layout: section
class: text-center
---

# Arquitectura

<div class="text-muted text-lg">Frontend React 19 · Backend FastAPI · Motor CTranslate2</div>

---
layout: two-cols
---

# Backend (FastAPI)

<div class="text-sm">

- **Routers**: `tokenize`, `analyze`, `translate`, `batch`, `config`
- **Services**:
  - `tokenizer.py` — tiktoken + langdetect
  - `translator.py` — CTranslate2
  - `ctranslate_service.py` — motor MarianMT
  - `clustering/` — intenciones 1–5 ⭐
  - `batch/` — io, columnas, economía, orquestación
- **Models** por dominio: `analyze`, `batch`, `config`

</div>

::right::

# Frontend (React 19)

<div class="text-sm">

- **Dark dashboard** moderno (Tailwind)
- **ExcelIngest** — orquestador principal
- `upload/` — drag & drop de archivo o carpeta
- `results/` — KPI grid, costos, ratings, tabla
- `hooks/useBatchProcessing` — estado y lógica
- `utils/` — formato y export a Excel (xlsx)

</div>

---
layout: default
---

# Motor de traducción

<div grid="~ cols-2 gap-6">

<div class="tb-card tb-card-accent">
  <div class="font-bold text-green">CTranslate2 / MarianMT</div>
  <ul class="text-sm mt-3 space-y-1 text-muted">
    <li>Modelo: <code>Helsinki-NLP/opus-mt-es-en</code></li>
    <li>CPU, INT8, multihilo (C++)</li>
    <li>100% local — sin API ni coste</li>
    <li>Convertido desde Hugging Face</li>
  </ul>
</div>

<div class="tb-card">
  <div class="font-bold text-indigo">Tokenización</div>
  <ul class="text-sm mt-3 space-y-1 text-muted">
    <li>Encoder <code>o200k_base</code></li>
    <li>Detección de idioma: langdetect</li>
    <li>Comparativa ES vs EN por intención</li>
    <li>Costo: $2.50 / millón de tokens</li>
  </ul>
</div>

</div>

---
layout: two-cols
---

# Ingesta de datos (Excel)

- **Archivo único** (`.xlsx`, `.csv`)
- **Carpeta completa** — sube todos los archivos
- Vista previa de las primeras filas
- Optimización de tokens opcional

::right::

# Resultados

- Agrupamiento en **5 intenciones** por producto
- Traducción del resumen de cada intención
- **KPIs**: ahorro diario, semanal, mensual y anual
- Comparativa de costos original vs inglés
- Rating promedio por producto ⭐
- Exportación a Excel (3 hojas)

---
layout: section
class: text-center
---

# Impacto económico

<div class="text-muted text-lg">Traducir cuesta menos que no traducir</div>

---
layout: two-cols
---

# Proyección a escala

<div class="text-sm">

- **10,000 reseñas/día** como referencia
- Costo: `$2.50 / 1M tokens`
- Promedio ES ≈ **27 tok** vs EN ≈ **19 tok**

</div>

<div class="tb-card tb-card-success mt-6">
  <div class="text-xs text-dim uppercase tracking-wide">Ahorro mensual</div>
  <div class="text-4xl font-bold text-green mt-1">$6.00</div>
  <div class="text-xs text-dim mt-1">(proyectado a 10k/día)</div>
</div>

::right::

<div class="tb-card">
  <div class="font-bold text-sm text-muted">KPIs por resultado</div>
  <ul class="text-sm mt-3 space-y-2 text-muted">
    <li>🕐 Ahorro diario</li>
    <li>📅 Ahorro semanal</li>
    <li>📆 Ahorro mensual</li>
    <li>📈 Ahorro anual (×12)</li>
  </ul>
  <div class="text-xs text-dim mt-4">El valor se calcula con el promedio real de tokens de cada proceso.</div>
</div>

---
layout: center
class: text-center
---

# Demo

Sube un Excel → analiza → descarga el resumen

<div class="pt-4 text-sm text-dim">Archivo de ejemplo: `backend/sample_reviews.xlsx`</div>

---
layout: center
class: text-center
---

# ¡Gracias!

**Token Bender** — menos tokens, más ahorro

<div class="pt-6 text-sm text-dim">stack: React 19 · FastAPI · CTranslate2 · tiktoken · Tailwind</div>
