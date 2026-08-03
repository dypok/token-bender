import { useBatchProcessing } from '../hooks/useBatchProcessing'
import Button from './Button'
import ConsoleWindow from './ConsoleWindow'
import UploadTabs from './upload/UploadTabs'
import FileUploadZone from './upload/FileUploadZone'
import FolderUploadZone from './upload/FolderUploadZone'
import KpiGrid from './results/KpiGrid'
import CostComparison from './results/CostComparison'
import ProductRatings from './results/ProductRatings'
import ResultsTable from './results/ResultsTable'
import { downloadExcel } from '../utils/excelExport'

export default function ExcelIngest() {
  const {
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
  } = useBatchProcessing()

  const handleModeChange = (next: 'file' | 'folder') => {
    setMode(next)
    resetOutputs()
    setConsoleVisible(false)
  }

  const handleDownload = () => downloadExcel(results, summary, productRatings)

  return (
    <div className="space-y-6">
      {/* Hero header */}
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-bold tracking-tight">Análisis de Reseñas</h1>
        <p className="text-sm text-[var(--text-muted)]">
          Carga un Excel de reseñas y traduce automáticamente al inglés con CTranslate2 para medir el ahorro de tokens.
        </p>
      </div>

      {/* Mode tabs */}
      <UploadTabs mode={mode} onChange={handleModeChange} />

      {/* Upload card */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">{mode === 'file' ? 'Cargar archivo Excel' : 'Procesar carpeta local'}</span>
          <label className="flex cursor-pointer items-center gap-2 text-sm text-[var(--text-muted)]">
            <input
              type="checkbox"
              checked={optimize}
              onChange={(e) => setOptimize(e.target.checked)}
              className="h-4 w-4 accent-indigo-500"
            />
            Optimizar tokens
          </label>
        </div>
        <div className="card-body space-y-4">
          {mode === 'file' ? (
            <FileUploadZone
              fileRef={fileRef}
              fileName={fileName}
              dragOver={dragOver}
              setDragOver={setDragOver}
              preview={preview}
              showPreview={!consoleVisible}
              onFileChange={handleFileChange}
              onFileDrop={handleFileDrop}
            />
          ) : (
            <FolderUploadZone
              folderRef={folderRef}
              folderName={folderName}
              folderFiles={folderFiles}
              dragOver={dragOver}
              setDragOver={setDragOver}
              onFolderChange={handleFolderChange}
              onFolderDrop={handleFolderDrop}
            />
          )}

          <div className="flex justify-end">
            <Button
              variant="primary"
              onClick={handleProcess}
              disabled={loading || !canProcess}
            >
              {loading ? (
                <>
                  <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  Procesando...
                </>
              ) : (
                <>
                  <span className="material-icons text-base">play_arrow</span>
                  Analizar
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Terminal */}
      <ConsoleWindow
        lines={consoleLines}
        visible={consoleVisible}
        onClose={() => setConsoleVisible(false)}
      />

      {/* Results */}
      {summary && <KpiGrid summary={summary} clusterCount={results.length} />}
      {summary && <CostComparison summary={summary} />}
      <ProductRatings ratings={productRatings} />
      <ResultsTable results={results} onDownload={handleDownload} />
    </div>
  )
}
