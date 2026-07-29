import { useState, useRef } from 'react'
import { useStore } from '../store/useStore'
import { uploadExcel, processFolder } from '../api/client'
import TitleBar from './TitleBar'
import Button from './Button'
import * as XLSX from 'xlsx'
import type { BatchResult, EconomicSummary } from '../types'

export default function ExcelIngest() {
  const { engine, deeplApiKey } = useStore()
  const [optimize, setOptimize] = useState(true)
  const [results, setResults] = useState<BatchResult[]>([])
  const [summary, setSummary] = useState<EconomicSummary | null>(null)
  const [loading, setLoading] = useState(false)
  const [preview, setPreview] = useState<string[][]>([])
  const [mode, setMode] = useState<'file' | 'folder'>('file')
  const [folderPath, setFolderPath] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

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
    setLoading(true)
    try {
      let data
      if (mode === 'file') {
        const file = fileRef.current?.files?.[0]
        if (!file) {
          alert('Por favor, selecciona un archivo Excel.')
          setLoading(false)
          return
        }
        data = await uploadExcel(file, optimize, engine, deeplApiKey)
      } else {
        if (!folderPath.trim()) {
          alert('Por favor, ingresa la ruta de la carpeta.')
          setLoading(false)
          return
        }
        data = await processFolder(folderPath.trim(), optimize, engine, deeplApiKey)
      }
      setResults(data.results)
      setSummary(data.economic_summary)
    } catch {
      setResults([])
      setSummary(null)
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadExcel = () => {
    const wb = XLSX.utils.book_new()

    const rows = results.map((r) => ({
      'Reseña original': r.review,
      'Costo tokens (reseña original)': `$${r.cost_original_usd.toFixed(8)}`,
      'Tokens original': r.tokens_original,
      'Reseña en inglés': r.text_en,
      'Costo tokens (inglés)': `$${r.cost_en_usd.toFixed(8)}`,
      'Tokens inglés': r.tokens_en,
      'Mejor idioma': r.best_lang === 'en' ? 'Inglés' : r.best_lang === 'es' ? 'Español' : 'Igual',
      'Justificación': r.justification,
      'Costo en español (USD)': `$${r.cost_original_usd.toFixed(8)}`,
      'Costo en inglés (USD)': `$${r.cost_en_usd.toFixed(8)}`,
      'Error type': r.classification?.error_type ?? '',
      'Component': r.classification?.component ?? '',
    }))
    const ws = XLSX.utils.json_to_sheet(rows)
    XLSX.utils.book_append_sheet(wb, ws, 'Análisis de costos')

    if (summary) {
      const summaryRows = [
        { Métrica: 'Total reseñas procesadas', Valor: summary.total_reviews },
        { Métrica: 'Total tokens (original)', Valor: summary.total_tokens_original },
        { Métrica: 'Total tokens (inglés)', Valor: summary.total_tokens_en },
        { Métrica: 'Promedio tokens por reseña (original)', Valor: summary.avg_tokens_original },
        { Métrica: 'Promedio tokens por reseña (inglés)', Valor: summary.avg_tokens_en },
        { Métrica: 'Costo diario original (10k res/día)', Valor: `$${summary.daily_cost_original_10k}` },
        { Métrica: 'Costo diario inglés (10k res/día)', Valor: `$${summary.daily_cost_en_10k}` },
        { Métrica: 'Ahorro diario (10k res/día)', Valor: `$${summary.daily_savings_10k}` },
        { Métrica: 'Ahorro semanal (10k res/día)', Valor: `$${summary.weekly_savings_10k}` },
        { Métrica: 'Ahorro mensual (10k res/día)', Valor: `$${summary.monthly_savings_10k}` },
        { Métrica: 'Mejor idioma global', Valor: summary.best_global_lang === 'en' ? 'Inglés' : 'Español' },
      ]
      XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(summaryRows), 'Proyección económica')
    }

    XLSX.writeFile(wb, 'analisis_costos_tokenopt.xlsx')
  }

  return (
    <div className="window w-[960px]">
      <TitleBar title="Excel Ingest — App Store Reviews" icon="description" />
      <div className="p-4 space-y-4">
        <div className="flex gap-2">
          <button
            className={`px-4 py-1.5 text-xs cursor-pointer rounded-t-md border border-b-0 ${
              mode === 'file'
                ? 'bg-white border-gray-300 font-semibold text-[var(--aero-end)] shadow-sm'
                : 'bg-gray-100 border-transparent text-gray-600 hover:bg-gray-200'
            }`}
            onClick={() => { setMode('file'); setResults([]); setSummary(null); setPreview([]); }}
          >
            Modo A: Archivo Único (.xlsx)
          </button>
          <button
            className={`px-4 py-1.5 text-xs cursor-pointer rounded-t-md border border-b-0 ${
              mode === 'folder'
                ? 'bg-white border-gray-300 font-semibold text-[var(--aero-end)] shadow-sm'
                : 'bg-gray-100 border-transparent text-gray-600 hover:bg-gray-200'
            }`}
            onClick={() => { setMode('folder'); setResults([]); setSummary(null); setPreview([]); }}
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
                  placeholder="Ej. /home/usuario/reseñas"
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

        {preview.length > 0 && (
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
            <div className="panel-header">Proyección de costos (10,000 reseñas/día)</div>
            <div className="grid grid-cols-3 gap-3 text-center text-xs mb-3">
              <div className="bg-red-50 rounded p-2">
                <div className="text-lg font-bold text-red-700">${summary.daily_cost_original_10k.toFixed(2)}</div>
                <div className="text-gray-600">Costo diario (original)</div>
              </div>
              <div className="bg-green-50 rounded p-2">
                <div className="text-lg font-bold text-green-700">${summary.daily_cost_en_10k.toFixed(2)}</div>
                <div className="text-gray-600">Costo diario (inglés)</div>
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
                <div className="text-base font-bold capitalize">{summary.best_global_lang === 'en' ? 'Inglés' : 'Español'}</div>
                <div className="text-gray-500">Mejor idioma global</div>
              </div>
            </div>
            <div className="text-xs text-gray-500 mt-2">
              {summary.total_reviews} reseñas · prom. {summary.avg_tokens_original} tok/res (esp) · {summary.avg_tokens_en} tok/res (eng)
            </div>
          </div>
        )}

        {results.length > 0 && (
          <div className="panel">
            <div className="panel-header flex items-center justify-between">
              <span>Resultados ({results.length} reseñas)</span>
              <Button onClick={handleDownloadExcel}>Descargar Excel</Button>
            </div>
            <div className="overflow-x-auto overflow-y-auto max-h-80 text-xs">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-gray-200 sticky top-0">
                    <th className="border border-gray-300 px-2 py-1 text-left">Reseña original</th>
                    <th className="border border-gray-300 px-2 py-1 w-16">Tok. ES</th>
                    <th className="border border-gray-300 px-2 py-1 w-20">Costo ES</th>
                    <th className="border border-gray-300 px-2 py-1 w-16">Tok. EN</th>
                    <th className="border border-gray-300 px-2 py-1 w-20">Costo EN</th>
                    <th className="border border-gray-300 px-2 py-1 w-16">Mejor</th>
                    <th className="border border-gray-300 px-2 py-1 w-20">Error</th>
                    <th className="border border-gray-300 px-2 py-1 w-24">Componente</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r, i) => {
                    const best = r.best_lang === 'en' ? 'Inglés' : r.best_lang === 'es' ? 'Español' : '='
                    return (
                      <tr key={i} className={i % 2 ? 'bg-gray-100' : ''}>
                        <td className="border border-gray-300 px-2 py-1 max-w-xs truncate" title={r.review}>{r.review}</td>
                        <td className="border border-gray-300 px-2 py-1 text-right">{r.tokens_original}</td>
                        <td className="border border-gray-300 px-2 py-1 text-right text-red-600">${r.cost_original_usd.toFixed(8)}</td>
                        <td className="border border-gray-300 px-2 py-1 text-right">{r.tokens_en}</td>
                        <td className="border border-gray-300 px-2 py-1 text-right text-green-600">${r.cost_en_usd.toFixed(8)}</td>
                        <td className={`border border-gray-300 px-2 py-1 font-semibold ${r.best_lang === 'en' ? 'text-green-700' : r.best_lang === 'es' ? 'text-red-700' : ''}`}>{best}</td>
                        <td className="border border-gray-300 px-2 py-1">{r.classification?.error_type ?? '—'}</td>
                        <td className="border border-gray-300 px-2 py-1">{r.classification?.component ?? '—'}</td>
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
