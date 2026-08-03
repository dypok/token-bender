import { useCallback, useRef, useState } from 'react'
import { processFolder as apiProcessFolder, startBatch, getBatchProgress } from '../api/client'
import type { ConsoleLine } from '../components/ConsoleWindow'
import * as XLSX from 'xlsx'
import type { BatchResult, EconomicSummary, BatchUploadResponse } from '../types'

export type UploadMode = 'file' | 'folder'

const SUPPORTED_EXT = /\.(xlsx|csv)$/i

export function folderNameFromFiles(files: File[]): string {
  const rel = files[0]?.webkitRelativePath
  if (rel && rel.includes('/')) return rel.split('/')[0]
  return files[0]?.name || 'Carpeta'
}

const logColor = (line: string): ConsoleLine['color'] =>
  line.startsWith('ERROR') ? 'red'
    : line.includes('✓') ? 'green'
    : line.includes('→') ? 'yellow'
    : line.includes('completado') ? 'green'
    : 'white'

export function useBatchProcessing() {
  const [optimize, setOptimize] = useState(true)
  const [results, setResults] = useState<BatchResult[]>([])
  const [summary, setSummary] = useState<EconomicSummary | null>(null)
  const [consoleLines, setConsoleLines] = useState<ConsoleLine[]>([])
  const [consoleVisible, setConsoleVisible] = useState(false)
  const [loading, setLoading] = useState(false)
  const [preview, setPreview] = useState<string[][]>([])
  const [mode, setMode] = useState<UploadMode>('file')
  const [folderFiles, setFolderFiles] = useState<File[]>([])
  const [folderName, setFolderName] = useState('')
  const [fileName, setFileName] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const [productRatings, setProductRatings] = useState<Record<string, number>>({})
  const fileRef = useRef<HTMLInputElement>(null)
  const folderRef = useRef<HTMLInputElement>(null)

  const addLog = useCallback((text: string, color?: ConsoleLine['color']) => {
    setConsoleLines((prev) => [...prev, { text, color }])
  }, [])

  const applyResult = (data: BatchUploadResponse) => {
    setResults(data.results)
    setSummary(data.economic_summary)
    if (data.product_ratings) setProductRatings(data.product_ratings)
  }

  const resetOutputs = () => {
    setResults([])
    setSummary(null)
    setConsoleLines([])
    setPreview([])
    setProductRatings({})
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setFileName(file.name)
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

  const handleFolderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (!files.length) return
    setFolderName(folderNameFromFiles(files))
    setFolderFiles(files.filter((f) => SUPPORTED_EXT.test(f.name)))
  }

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file && fileRef.current) {
      const dt = new DataTransfer()
      dt.items.add(file)
      fileRef.current.files = dt.files
      handleFileChange({ target: fileRef.current } as unknown as React.ChangeEvent<HTMLInputElement>)
    }
  }

  const handleFolderDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const files = Array.from(e.dataTransfer.files || [])
    if (files.length) {
      setFolderName(folderNameFromFiles(files))
      setFolderFiles(files.filter((f) => SUPPORTED_EXT.test(f.name)))
    }
  }

  const processSingleFile = async (): Promise<BatchUploadResponse | null> => {
    const file = fileRef.current?.files?.[0]
    if (!file) {
      addLog('ERROR: No se seleccionó ningún archivo.', 'red')
      return null
    }
    addLog(`Procesando archivo: ${file.name}`, 'white')

    try {
      const taskId = await startBatch(file, optimize)
      addLog(`Task ID: ${taskId}`, 'white')
      addLog('')

      let done = false
      let resultData: BatchUploadResponse | null = null
      let lastLogCount = 0

      while (!done) {
        await new Promise((r) => setTimeout(r, 1500))
        const progress = await getBatchProgress(taskId)
        done = progress.done
        resultData = progress.result

        for (let i = lastLogCount; i < progress.logs.length; i++) {
          addLog(progress.logs[i], logColor(progress.logs[i]))
        }
        lastLogCount = progress.logs.length
      }

      if (!resultData) {
        addLog('ERROR: El servidor reportó un error durante la ejecución del proceso en lote.', 'red')
        return null
      }
      return resultData
    } catch (err: any) {
      addLog(`ERROR: Falló el procesamiento batch: ${err?.message || err}`, 'red')
      return null
    }
  }

  const processFolder = async (): Promise<BatchUploadResponse | null> => {
    if (!folderFiles.length) {
      addLog('ERROR: No se seleccionó ninguna carpeta.', 'red')
      return null
    }
    addLog(`Procesando carpeta: ${folderName} (${folderFiles.length} archivos)`, 'white')
    try {
      return await apiProcessFolder(folderFiles, optimize)
    } catch {
      addLog('ERROR: Falló el procesamiento de la carpeta.', 'red')
      return null
    }
  }

  const handleProcess = async () => {
    setLoading(true)
    setConsoleVisible(true)
    setResults([])
    setSummary(null)
    setConsoleLines([])

    addLog('Iniciando procesamiento batch...', 'cyan')

    const start = performance.now()
    const data = mode === 'file' ? await processSingleFile() : await processFolder()

    if (data) {
      applyResult(data)
      const elapsed = Math.round(performance.now() - start)
      addLog('')
      addLog(`Procesamiento completado en ${elapsed}ms`, 'green')
      addLog(`Total reseñas: ${data.economic_summary.total_reviews}`, 'white')
      const savings = data.economic_summary.monthly_savings_10k
      addLog(`Ahorro mensual estimado: $${savings.toFixed(2)}`, savings > 0 ? 'green' : 'gray')
      addLog('Proceso completado.', 'green')
    }

    setLoading(false)
  }

  const canProcess =
    (mode === 'file' && !!fileRef.current?.files?.[0]) ||
    (mode === 'folder' && folderFiles.length > 0)

  return {
    optimize, setOptimize,
    mode, setMode,
    results, summary, productRatings,
    consoleLines, consoleVisible, setConsoleVisible,
    loading,
    preview,
    fileName, folderName, folderFiles,
    dragOver, setDragOver,
    fileRef, folderRef,
    resetOutputs,
    handleFileChange, handleFolderChange,
    handleFileDrop, handleFolderDrop,
    handleProcess,
    canProcess,
  }
}
