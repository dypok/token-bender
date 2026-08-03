import type { RefObject } from 'react'

interface Props {
  fileRef: RefObject<HTMLInputElement | null>
  fileName: string
  dragOver: boolean
  setDragOver: (v: boolean) => void
  preview: string[][]
  showPreview: boolean
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  onFileDrop: (e: React.DragEvent) => void
}

export default function FileUploadZone({
  fileRef, fileName, dragOver, setDragOver, preview, showPreview,
  onFileChange, onFileDrop,
}: Props) {
  return (
    <>
      <div
        className={`drop-zone ${dragOver ? 'drop-zone-drag' : ''}`}
        onClick={() => fileRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onFileDrop}
      >
        <input
          ref={fileRef}
          type="file"
          accept=".xlsx,.csv"
          onChange={onFileChange}
          className="hidden"
        />
        <span className="material-icons text-4xl text-[var(--accent)]">cloud_upload</span>
        <div className="mt-3 text-sm font-medium text-[var(--text)]">
          {fileName || 'Arrastra tu archivo .xlsx aquí o haz clic para elegir'}
        </div>
        <div className="mt-1 text-xs text-[var(--text-dim)]">Formatos soportados: .xlsx, .csv</div>
      </div>

      {showPreview && preview.length > 0 && (
        <div className="overflow-x-auto">
          <table className="table">
            <thead>
              <tr>
                {preview[0].map((h, i) => <th key={i}>{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {preview.slice(1).map((row, ri) => (
                <tr key={ri}>
                  {row.map((cell, ci) => <td key={ci}>{cell}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
