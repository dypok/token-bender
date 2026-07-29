import { useState, useRef, useCallback } from 'react'
import { useStore } from '../store/useStore'
import { uploadExcel, processFolder, analyzeText } from '../api/client'
import TitleBar from './TitleBar'
import Button from './Button'
import ConsoleWindow from './ConsoleWindow'
import type { ConsoleLine } from './ConsoleWindow'
import * as XLSX from 'xlsx'
import type { BatchResult, EconomicSummary, AnalyzeResponse } from '../types'

const COST_PER_MILLION = 2.5
const REVIEWS_10K = 10000

function makeBatchItem(text: string, resp: AnalyzeResponse): BatchResult {
  const tokEs = resp.original.token_count
  const tokEn = resp.translated.token_count
  const costEs = (tokEs / 1_000_000) * COST_PER_MILLION
  const costEn = (tokEn / 1_000_000) * COST_PER_MILLION
  const diff = tokEn - tokEs
  let best: string, just: string
  if (diff < 0) {
    best = 'en'
    just = `Inglés tiene ${Math.abs(diff)} tokens menos que español ($${Math.abs(costEn - costEs).toFixed(6)} más barato)`
  } else if (diff > 0) {
    best = 'es'
    just = `Español tiene ${diff} tokens menos que inglés ($${Math.abs(costEs - costEn).toFixed(6)} más barato)`
  } else {
    best = 'igual'
    just = 'Ambos idiomas tienen el mismo costo de tokens'
  }
  return {
    review: text,
    tokens_original: tokEs,
    text_en: resp.translated.text,
    tokens_en: tokEn,
    cost_original_usd: costEs,
    cost_en_usd: costEn,
    best_lang: best,
    justification: just,
    classification: resp.classification ?? undefined,
  }
}

function buildSummary(items: BatchResult[]): EconomicSummary {
  const total = items.length
  if (total === 0) {
    return {
      total_reviews: 0, total_tokens_original: 0, total_tokens_en: 0,
      avg_tokens_original: 0, avg_tokens_en: 0,
      daily_cost_original_10k: 0, daily_cost_en_10k: 0,
      daily_savings_10k: 0, weekly_savings_10k: 0, monthly_savings_10k: 0,
      best_global_lang: 'es',
    }
  }
  const sumOrig = items.reduce((a, r) => a + r.tokens_original, 0)
  const sumEn = items.reduce((a, r) => a + r.tokens_en, 0)
  const avgOrig = Math.round(sumOrig / total)
  const avgEn = Math.round(sumEn / total)
  const dailyOrig = (avgOrig / 1_000_000) * COST_PER_MILLION * REVIEWS_10K
  const dailyEn = (avgEn / 1_000_000) * COST_PER_MILLION * REVIEWS_10K
  const dailySavings = dailyOrig - dailyEn
  const enBetter = items.filter((r) => r.best_lang === 'en').length
  const esBetter = items.filter((r) => r.best_lang === 'es').length
  return {
    total_reviews: total,
    total_tokens_original: sumOrig,
    total_tokens_en: sumEn,
    avg_tokens_original: avgOrig,
    avg_tokens_en: avgEn,
    daily_cost_original_10k: Math.round(dailyOrig * 100) / 100,
    daily_cost_en_10k: Math.round(dailyEn * 100) / 100,
    daily_savings_10k: Math.round(Math.max(0, dailySavings) * 100) / 100,
    weekly_savings_10k: Math.round(Math.max(0, dailySavings * 7) * 100) / 100,
    monthly_savings_10k: Math.round(Math.max(0, dailySavings * 30) * 100) / 100,
    best_global_lang: enBetter >= esBetter ? 'en' : 'es',
  }
}

export default function ExcelIngest() {
  const { engine, deeplApiKey } = useStore()
  const [optimize, setOptimize] = useState(true)
  const [results, setResults] = useState<BatchResult[]>([])
  const [summary, setSummary] = useState<EconomicSummary | null>(null)
  const [consoleLines, setConsoleLines] = useState<ConsoleLine[]>([])
  const [consoleVisible, setConsoleVisible] = useState(false)
  const [loading, setLoading] = useState(false)
  const [preview, setPreview] = useState<string[][]>([])
  const [mode, setMode] = useState<'file' | 'folder'>('file')
  const [folderPath, setFolderPath] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)
  const abortRef = useRef(false)

  const addLog = useCallback((text: string, color?: ConsoleLine['color']) => {
    setConsoleLines((prev) => [...prev, { text, color }])
  }, [])

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (evt) => {
      const data = new Uint8Array(evt.target?.result as ArrayBuffer)
      const workbook = XLSX.read(data, { type: 'array' })
      const sheet = workbook.Sheets[workbook.SheetNames[0]]
      const rows = XLSX.utils.sheet_to_json<string[]>(sheet, { header: 1 })
      setPreview(rows.slice(0, 5))
    }
    reader.readAsArrayBuffer(file)
  }

  const handleProcess = async () => {
    abortRef.current = false
    setLoading(true)
    setConsoleVisible(true)
    setConsoleLines([])
    setResults([])
    setSummary(null)

    addLog('Microsoft Windows [Versi\u00f3n 6.1.7601]', 'gray')
    addLog('Copyright (c) 2009 Microsoft Corporation. Todos los derechos reservados.', 'gray')
    addLog('')

    let rows: string[][] = []

    if (mode === 'file') {
      const file = fileRef.current?.files?.[0]
      if (!file) {
        addLog('ERROR: No se seleccion\u00f3 ning\u00fan archivo.', 'red')
        setLoading(false)
        return
      }
      addLog(`C:\\&gt; Procesando archivo: ${file.name}`, 'cyan')
      const data = new Uint8Array(await file.arrayBuffer())
      const workbook = XLSX.read(data, { type: 'array' })
      const sheet = workbook.Sheets[workbook.SheetNames[0]]
      rows = XLSX.utils.sheet_to_json<string[]>(sheet, { header: 1 })
    } else {
      if (!folderPath.trim()) {
        addLog('ERROR: No se especific\u00f3 ruta de carpeta.', 'red')
        setLoading(false)
        return
      }
      addLog(`C:\\&gt; Escaneando carpeta: ${folderPath}`, 'cyan')
      try {
        const data = await processFolder(folderPath.trim(), optimize, engine, deeplApiKey)
        setResults(data.results)
        setSummary(data.economic_summary)
        addLog('')
        addLog(`Procesados ${data.results.length} archivos (v\u00eda servidor).`, 'green')
        addLog('')
        setLoading(false)
        return
      } catch {
        addLog('ERROR: Fall\u00f3 el procesamiento de la carpeta.', 'red')
        setLoading(false)
        return
      }
    }

    const textCol = _detectTextColumn(rows)
    if (!textCol) {
      addLog('ERROR: No se pudo detectar la columna de rese\u00f1as.', 'red')
      setLoading(false)
      return
    }

    const reviews = rows.slice(1).map((r) => String(r[textCol] ?? '')).filter(Boolean)
    addLog(`Leidas ${reviews.length} rese\u00f1as desde la columna "${rows[0][textCol]}"`)
    addLog('')
    addLog(`Iniciando procesamiento concurrente (lotes de hasta 2 en paralelo)`, 'cyan')
    addLog('')

    const batchItems: BatchResult[] = []
    const CONCURRENCY = 2

    async function processOne(review: string, index: number): Promise<{ logs: ConsoleLine[]; item: BatchResult | null }> {
      const logs: ConsoleLine[] = []
      const push = (text: string, color?: ConsoleLine['color']) => logs.push({ text, color })
      const startTime = performance.now()

      push(`[${index + 1}/${reviews.length}] "${review.slice(0, 60)}${review.length > 60 ? '...' : ''}"`, 'yellow')

      try {
        push('  \u2514 Analizando...', 'gray')
        const resp = await analyzeText(review, engine, deeplApiKey, true, true)
        push(`  \u2514 ES: ${resp.original.token_count} tok | EN: ${resp.translated.token_count} tok (${resp.engine_used})`, 'gray')

        if (resp.classification) {
          push(`  \u2514 error=${resp.classification.error_type}, componente=${resp.classification.component}`, 'green')
        }

        const elapsed = Math.round(performance.now() - startTime)
        const saved = resp.original.token_count - resp.translated.token_count
        push(`  \u2713 ${elapsed}ms (ahorro: ${saved > 0 ? saved : 'ninguno'} tokens)`, saved > 0 ? 'green' : 'gray')
        push('')

        return { logs, item: makeBatchItem(review, resp) }
      } catch {
        const elapsed = Math.round(performance.now() - startTime)
        push(`  \u2717 ERROR (${elapsed}ms)`, 'red')
        push('')
        return { logs, item: null }
      }
    }

    for (let i = 0; i < reviews.length; i += CONCURRENCY) {
      if (abortRef.current) break
      const batch = reviews.slice(i, i + CONCURRENCY)
      const results = await Promise.all(batch.map((review, idx) => processOne(review, i + idx)))

      for (const r of results) {
        for (const line of r.logs) {
          addLog(line.text, line.color)
        }
        if (r.item) batchItems.push(r.item)
      }
    }

    if (batchItems.length > 0) {
      const s = buildSummary(batchItems)
      setResults(batchItems)
      setSummary(s)

      addLog('--- RESUMEN ECON\u00d3MICO ---', 'cyan')
      addLog(`Total rese\u00f1as: ${s.total_reviews}`, 'white')
      addLog(`Tokens original (total): ${s.total_tokens_original}`, 'white')
      addLog(`Tokens ingl\u00e9s (total): ${s.total_tokens_en}`, 'white')
      addLog(`Promedio tokens/rese\u00f1a (ES): ${s.avg_tokens_original}`, 'white')
      addLog(`Promedio tokens/rese\u00f1a (EN): ${s.avg_tokens_en}`, 'white')
      addLog('')
      addLog(`Costo diario original (10k res/d\u00eda): $${s.daily_cost_original_10k.toFixed(2)}`, 'yellow')
      addLog(`Costo diario ingl\u00e9s (10k res/d\u00eda):   $${s.daily_cost_en_10k.toFixed(2)}`, 'yellow')
      addLog(`Ahorro mensual estimado:                 $${s.monthly_savings_10k.toFixed(2)}`, s.monthly_savings_10k > 0 ? 'green' : 'gray')
      addLog('')
      addLog('C:\\&gt; Proceso completado.', 'green')
    } else {
      addLog('No se procesaron rese\u00f1as.', 'red')
    }

    setLoading(false)
  }

  const handleDownloadExcel = () => {
    const wb = XLSX.utils.book_new()
    const r = results.map((r) => ({
      'Rese\u00f1a original': r.review,
      'Tokens original': r.tokens_original,
      'Rese\u00f1a en ingl\u00e9s': r.text_en,
      'Tokens ingl\u00e9s': r.tokens_en,
      'Mejor idioma': r.best_lang === 'en' ? 'Ingl\u00e9s' : r.best_lang === 'es' ? 'Espa\u00f1ol' : 'Igual',
      'Justificaci\u00f3n': r.justification,
      'Error type': r.classification?.error_type ?? '',
      'Component': r.classification?.component ?? '',
    }))
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(r), 'An\u00e1lisis de costos')
    if (summary) {
      XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet([
        { M\u00e9trica: 'Total rese\u00f1as procesadas', Valor: summary.total_reviews },
        { M\u00e9trica: 'Total tokens (original)', Valor: summary.total_tokens_original },
        { M\u00e9trica: 'Total tokens (ingl\u00e9s)', Valor: summary.total_tokens_en },
        { M\u00e9trica: 'Promedio tokens/rese\u00f1a (original)', Valor: summary.avg_tokens_original },
        { M\u00e9trica: 'Promedio tokens/rese\u00f1a (ingl\u00e9s)', Valor: summary.avg_tokens_en },
        { M\u00e9trica: 'Costo diario original (10k res/d\u00eda)', Valor: `$${summary.daily_cost_original_10k}` },
        { M\u00e9trica: 'Costo diario ingl\u00e9s (10k res/d\u00eda)', Valor: `$${summary.daily_cost_en_10k}` },
        { M\u00e9trica: 'Ahorro diario (10k res/d\u00eda)', Valor: `$${summary.daily_savings_10k}` },
        { M\u00e9trica: 'Ahorro mensual (10k res/d\u00eda)', Valor: `$${summary.monthly_savings_10k}` },
      ]), 'Proyecci\u00f3n econ\u00f3mica')
    }
    XLSX.writeFile(wb, 'analisis_costos_tokenopt.xlsx')
  }

  return (
    <div className="window w-[960px]">
      <TitleBar title="Excel Ingest — App Store Reviews" icon="description" />
      <div className="p-4 space-y-4">
        {/* Mode tabs */}
        <div className="flex gap-2">
          <button
            className={`px-4 py-1.5 text-xs cursor-pointer rounded-t-md border border-b-0 ${
              mode === 'file'
                ? 'bg-white border-gray-300 font-semibold text-[var(--aero-end)] shadow-sm'
                : 'bg-gray-100 border-transparent text-gray-600 hover:bg-gray-200'
            }`}
            onClick={() => { setMode('file'); setResults([]); setSummary(null); setPreview([]); setConsoleVisible(false); }}
          >
            Modo A: Archivo \u00danico (.xlsx)
          </button>
          <button
            className={`px-4 py-1.5 text-xs cursor-pointer rounded-t-md border border-b-0 ${
              mode === 'folder'
                ? 'bg-white border-gray-300 font-semibold text-[var(--aero-end)] shadow-sm'
                : 'bg-gray-100 border-transparent text-gray-600 hover:bg-gray-200'
            }`}
            onClick={() => { setMode('folder'); setResults([]); setSummary(null); setPreview([]); setConsoleVisible(false); }}
          >
            Modo B: Lote en Carpeta
          </button>
        </div>

        <div className="panel !rounded-tl-none">
          <div className="panel-header">
            {mode === 'file' ? 'Cargar Archivo Excel' : 'Procesar Carpeta Local (Servidor)'}
          </div>
          <div className="flex gap-4 items-center p-2">
            {mode === 'file' ? (
              <input
                ref={fileRef}
                type="file"
                accept=".xlsx,.csv"
                onChange={handleFile}
                className="text-xs flex-1"
              />
            ) : (
              <div className="flex-1 flex gap-2 items-center">
                <span className="text-xs text-gray-600 font-medium shrink-0">Ruta de carpeta:</span>
                <input
                  type="text"
                  placeholder="Ej. /home/usuario/rese\u00f1as"
                  value={folderPath}
                  onChange={(e) => setFolderPath(e.target.value)}
                  className="input-aero flex-1 text-xs px-2 py-1"
                />
              </div>
            )}
            <div className="flex items-center gap-3 text-xs shrink-0">
              <label className="flex items-center gap-1 cursor-pointer">
                <input type="checkbox" checked={optimize} onChange={(e) => setOptimize(e.target.checked)} />
                Optimizar tokens
              </label>
              <Button onClick={handleProcess} disabled={loading}>
                {loading ? 'Procesando...' : 'Analizar'}
              </Button>
            </div>
          </div>
        </div>

        {/* Console */}
        <ConsoleWindow
          lines={consoleLines}
          visible={consoleVisible}
          onClose={() => setConsoleVisible(false)}
        />

        {preview.length > 0 && !consoleVisible && (
          <div className="panel">
            <div className="panel-header">Vista previa (primeras filas)</div>
            <div className="overflow-x-auto text-xs">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-gray-200">
                    {preview[0].map((h, i) => <th key={i} className="border border-gray-300 px-2 py-1 text-left">{h}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {preview.slice(1).map((row, ri) => (
                    <tr key={ri}>
                      {row.map((cell, ci) => <td key={ci} className="border border-gray-300 px-2 py-1">{cell}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {summary && (
          <div className="panel">
            <div className="panel-header">Proyecci\u00f3n de costos (10,000 rese\u00f1as/d\u00eda)</div>
            <div className="grid grid-cols-3 gap-3 text-center text-xs mb-3">
              <div className="bg-red-50 rounded p-2">
                <div className="text-lg font-bold text-red-700">${summary.daily_cost_original_10k.toFixed(2)}</div>
                <div className="text-gray-600">Costo diario (original)</div>
              </div>
              <div className="bg-green-50 rounded p-2">
                <div className="text-lg font-bold text-green-700">${summary.daily_cost_en_10k.toFixed(2)}</div>
                <div className="text-gray-600">Costo diario (ingl\u00e9s)</div>
              </div>
              <div className="bg-blue-50 rounded p-2">
                <div className="text-lg font-bold text-[var(--aero-end)]">${summary.daily_savings_10k.toFixed(2)}</div>
                <div className="text-gray-600">Ahorro diario</div>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3 text-center text-xs">
              <div>
                <div className="text-base font-bold">${summary.weekly_savings_10k.toFixed(2)}</div>
                <div className="text-gray-500">Ahorro semanal</div>
              </div>
              <div>
                <div className="text-base font-bold">${summary.monthly_savings_10k.toFixed(2)}</div>
                <div className="text-gray-500">Ahorro mensual</div>
              </div>
              <div>
                <div className="text-base font-bold capitalize">{summary.best_global_lang === 'en' ? 'Ingl\u00e9s' : 'Espa\u00f1ol'}</div>
                <div className="text-gray-500">Mejor idioma global</div>
              </div>
            </div>
            <div className="text-xs text-gray-500 mt-2">
              {summary.total_reviews} rese\u00f1as &middot; prom. {summary.avg_tokens_original} tok/res (esp) &middot; {summary.avg_tokens_en} tok/res (eng)
            </div>
          </div>
        )}

        {results.length > 0 && (
          <div className="panel">
            <div className="panel-header flex items-center justify-between">
              <span>Resultados ({results.length} rese\u00f1as)</span>
              <Button onClick={handleDownloadExcel}>Descargar Excel</Button>
            </div>
            <div className="overflow-x-auto overflow-y-auto max-h-80 text-xs">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-gray-200 sticky top-0">
                    <th className="border border-gray-300 px-2 py-1 text-left">Rese\u00f1a original</th>
                    <th className="border border-gray-300 px-2 py-1 text-left">Traducci\u00f3n (EN)</th>
                    <th className="border border-gray-300 px-2 py-1 w-16">Tok. ES</th>
                    <th className="border border-gray-300 px-2 py-1 w-16">Tok. EN</th>
                    <th className="border border-gray-300 px-2 py-1 w-16">Mejor</th>
                    <th className="border border-gray-300 px-2 py-1 w-20">Error</th>
                    <th className="border border-gray-300 px-2 py-1 w-24">Componente</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r, i) => {
                    const best = r.best_lang === 'en' ? 'Ingl\u00e9s' : r.best_lang === 'es' ? 'Espa\u00f1ol' : '='
                    return (
                      <tr key={i} className={i % 2 ? 'bg-gray-100' : ''}>
                        <td className="border border-gray-300 px-2 py-1 max-w-xs truncate" title={r.review}>{r.review}</td>
                        <td className="border border-gray-300 px-2 py-1 max-w-xs truncate" title={r.text_en}>{r.text_en}</td>
                        <td className="border border-gray-300 px-2 py-1 text-right">{r.tokens_original}</td>
                        <td className="border border-gray-300 px-2 py-1 text-right">{r.tokens_en}</td>
                        <td className={`border border-gray-300 px-2 py-1 font-semibold ${r.best_lang === 'en' ? 'text-green-700' : r.best_lang === 'es' ? 'text-red-700' : ''}`}>{best}</td>
                        <td className="border border-gray-300 px-2 py-1">{r.classification?.error_type ?? '\u2014'}</td>
                        <td className="border border-gray-300 px-2 py-1">{r.classification?.component ?? '\u2014'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function _detectTextColumn(rows: string[][]): number | null {
  if (rows.length < 1) return null
  const headers = rows[0].map((h) => String(h).toLowerCase().replace('ñ', 'n'))
  for (let i = 0; i < headers.length; i++) {
    if (['review', 'reseña', 'rese', 'text', 'feedback', 'coment', 'opinion', 'comentario'].some((k) => headers[i].includes(k))) {
      return i
    }
  }
  return 0
}
