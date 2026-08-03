import type { RefObject } from 'react'

interface Props {
  folderRef: RefObject<HTMLInputElement | null>
  folderName: string
  folderFiles: File[]
  dragOver: boolean
  setDragOver: (v: boolean) => void
  onFolderChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  onFolderDrop: (e: React.DragEvent) => void
}

export default function FolderUploadZone({
  folderRef, folderName, folderFiles, dragOver, setDragOver,
  onFolderChange, onFolderDrop,
}: Props) {
  return (
    <>
      <div
        className={`drop-zone ${dragOver ? 'drop-zone-drag' : ''}`}
        onClick={() => folderRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onFolderDrop}
      >
        <input
          ref={folderRef}
          type="file"
          {...{ webkitdirectory: '' }}
          onChange={onFolderChange}
          className="hidden"
        />
        <span className="material-icons text-4xl text-[var(--accent)]">create_new_folder</span>
        <div className="mt-3 text-sm font-medium text-[var(--text)]">
          {folderName || 'Selecciona una carpeta con tus archivos Excel'}
        </div>
        <div className="mt-1 text-xs text-[var(--text-dim)]">
          {folderFiles.length > 0
            ? `${folderFiles.length} archivos .xlsx/.csv encontrados`
            : 'Se procesarán todos los archivos .xlsx y .csv de la carpeta'}
        </div>
      </div>

      {folderFiles.length > 0 && (
        <div className="flex max-h-32 flex-wrap gap-2 overflow-y-auto">
          {folderFiles.slice(0, 12).map((f, i) => (
            <span key={i} className="badge bg-[var(--bg-hover)] text-[var(--text-muted)]">
              <span className="material-icons text-xs">insert_drive_file</span>
              {f.name}
            </span>
          ))}
          {folderFiles.length > 12 && (
            <span className="badge bg-[var(--bg-hover)] text-[var(--text-muted)]">
              +{folderFiles.length - 12} más
            </span>
          )}
        </div>
      )}
    </>
  )
}
