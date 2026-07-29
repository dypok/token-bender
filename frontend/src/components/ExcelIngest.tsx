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

  const handleExport = () => {
    const wb = XLSX.utils.book_new()
    const data = results.map((r) => ({
      Review: r.review,
      Tokens: r.tokens,
      ErrorType: r.classification?.error_type ?? '',
      Component: r.classification?.component ?? '',
    }))
    const ws = XLSX.utils.json_to_sheet(data)
    XLSX.utils.book_append_sheet(wb, ws, 'Results')

    if (summary) {
      const summarySheet = XLSX.utils.json_to_sheet([{
        Metric: 'Total reviews',
        Value: summary.total_reviews,
      }, {
        Metric: 'Total tokens processed',
        Value: summary.total_tokens_processed,
      }, {
        Metric: 'Avg tokens per review',
        Value: summary.avg_tokens_per_review,
      }, {
        Metric: 'Projected daily tokens (10k reviews)',
        Value: summary.projected_daily_tokens_10k,
      }, {
        Metric: 'Projected monthly tokens (10k reviews)',
        Value: summary.projected_monthly_tokens_10k,
      }, {
        Metric: 'Projected monthly savings USD (10k reviews)',
        Value: summary.projected_monthly_savings_usd_10k,
      }])
      XLSX.utils.book_append_sheet(wb, summarySheet, 'Economic Summary')
    }

    XLSX.writeFile(wb, 'analysis-results.xlsx')
  }

  return (
    <div className="window w-[900px]">
      <TitleBar title="Excel Ingest — App Store Reviews" icon="description" />
      <div className="p-4 space-y-4">
        {/* Selection mode */}
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

        {/* Upload/Folder controls */}
        <div className="panel !rounded-tl-none">
          <div className="panel-header">
            {mode === 'file' ? 'Cargar Archivo Excel' : 'Procesar Carpeta Local (Servidor)'}
          </div>
          <div className="flex gap-4 items-center p-2">
            {mode === 'file' ? (
              <input
                ref={fileRef}
                type="file"
                accept=".xlsx"
                onChange={handleFile}
                className="text-xs flex-1"
              />
            ) : (
              <div className="flex-1 flex gap-2 items-center">
                <span className="text-xs text-gray-600 font-medium shrink-0">Ruta de carpeta:</span>
                <input
                  type="text"
                  placeholder="Ej. C:/Users/Usuario/Documentos/Reseñas"
                  value={folderPath}
                  onChange={(e) => setFolderPath(e.target.value)}
                  className="input-aero flex-1 text-xs px-2 py-1"
                />
              </div>
            )}
            <div className="flex items-center gap-3 text-xs shrink-0">
              <label className="flex items-center gap-1 cursor-pointer">
                <input type="checkbox" checked={optimize} onChange={(e) => setOptimize(e.target.checked)} />
                Optimizar tokens (Traducir a Inglés)
              </label>
              <Button onClick={handleProcess} disabled={loading}>
                {loading ? 'Procesando...' : 'Analizar'}
              </Button>
            </div>
          </div>
        </div>

        {/* Preview */}
        {preview.length > 0 && (
          <div className="panel">
            <div className="panel-header">Preview (first rows)</div>
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

        {/* Economic Summary */}
        {summary && (
          <div className="panel">
            <div className="panel-header">Economic Projection (at 10,000 reviews/day)</div>
            <div className="grid grid-cols-3 gap-3 text-center text-xs">
              <div>
                <div className="text-lg font-bold text-[var(--aero-end)]">{summary.projected_daily_tokens_10k.toLocaleString()}</div>
                <div className="text-gray-600">Daily tokens</div>
              </div>
              <div>
                <div className="text-lg font-bold text-[var(--aero-end)]">{summary.projected_monthly_tokens_10k.toLocaleString()}</div>
                <div className="text-gray-600">Monthly tokens</div>
              </div>
              <div>
                <div className="text-lg font-bold text-green-700">${summary.projected_monthly_savings_usd_10k.toFixed(2)}</div>
                <div className="text-gray-600">Monthly savings (USD)</div>
              </div>
            </div>
            <div className="text-xs text-gray-500 mt-2">
              {summary.total_reviews} reviews · {summary.total_tokens_processed.toLocaleString()} tokens · avg {summary.avg_tokens_per_review} tokens/review
            </div>
          </div>
        )}

        {/* Results table */}
        {results.length > 0 && (
          <div className="panel">
            <div className="panel-header flex items-center justify-between">
              <span>Results ({results.length} reviews)</span>
              <Button onClick={handleExport}>Export to Excel</Button>
            </div>
            <div className="overflow-y-auto max-h-72 text-xs">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-gray-200 sticky top-0">
                    <th className="border border-gray-300 px-2 py-1 text-left">Review</th>
                    <th className="border border-gray-300 px-2 py-1 w-16">Tokens</th>
                    <th className="border border-gray-300 px-2 py-1 w-20">Error</th>
                    <th className="border border-gray-300 px-2 py-1 w-24">Component</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r, i) => (
                    <tr key={i} className={i % 2 ? 'bg-gray-100' : ''}>
                      <td className="border border-gray-300 px-2 py-1">{r.review}</td>
                      <td className="border border-gray-300 px-2 py-1 text-right">{r.tokens}</td>
                      <td className="border border-gray-300 px-2 py-1">{r.classification?.error_type ?? '—'}</td>
                      <td className="border border-gray-300 px-2 py-1">{r.classification?.component ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
