import type { UploadMode } from '../../hooks/useBatchProcessing'

interface Props {
  mode: UploadMode
  onChange: (mode: UploadMode) => void
}

export default function UploadTabs({ mode, onChange }: Props) {
  return (
    <div className="flex items-center gap-2">
      <button
        className={`tab ${mode === 'file' ? 'tab-active' : ''}`}
        onClick={() => onChange('file')}
      >
        <span className="material-icons align-middle text-base mr-1">upload_file</span>
        Archivo único
      </button>
      <button
        className={`tab ${mode === 'folder' ? 'tab-active' : ''}`}
        onClick={() => onChange('folder')}
      >
        <span className="material-icons align-middle text-base mr-1">folder</span>
        Carpeta completa
      </button>
    </div>
  )
}
