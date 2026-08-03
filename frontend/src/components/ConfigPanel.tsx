import { useEffect, useState } from 'react'
import { getConfigStatus } from '../api/client'
import Button from './Button'
import type { ConfigStatus } from '../types'

interface Props {
  onClose: () => void
}

export default function ConfigPanel({ onClose }: Props) {
  const [status, setStatus] = useState<ConfigStatus | null>(null)

  useEffect(() => {
    getConfigStatus().then(setStatus).catch(() => setStatus(null))
  }, [])

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="card w-[420px] max-w-[92vw]" onClick={(e) => e.stopPropagation()}>
        <div className="card-header">
          <span className="flex items-center gap-2">
            <span className="material-icons text-[var(--accent)]">settings</span>
            <span className="card-title">Configuración</span>
          </span>
          <button
            onClick={onClose}
            className="cursor-pointer rounded-lg p-1.5 text-[var(--text-dim)] hover:bg-[var(--bg-hover)] hover:text-[var(--text)]"
            title="Cerrar"
          >
            <span className="material-icons text-lg">close</span>
          </button>
        </div>

        <div className="card-body space-y-4">
          <div>
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-[var(--text-dim)]">Motor de traducción</div>
            <div className="flex items-center gap-3 rounded-xl border border-[var(--border)] bg-[var(--bg-elevated)] p-4">
              <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${status?.model_ready ? 'bg-emerald-500/15 text-emerald-400' : 'bg-slate-500/15 text-slate-400'}`}>
                <span className="material-icons">{status?.model_ready ? 'check_circle' : 'radio_button_unchecked'}</span>
              </div>
              <div className="flex-1">
                <div className="text-sm font-semibold">CTranslate2 / MarianMT</div>
                <div className="text-xs text-[var(--text-dim)]">
                  {status?.model_ready ? 'Motor disponible' : 'No disponible'}
                </div>
              </div>
              {status?.model_ready && (
                <span className="badge bg-emerald-500/15 text-emerald-400">Activo</span>
              )}
            </div>
            <p className="mt-2 text-[11px] leading-relaxed text-[var(--text-dim)]">
              Traducción local CPU (ES → EN) usando el modelo Helsinki-NLP opus-mt-es-en convertido a CTranslate2.
            </p>
          </div>

          <div className="flex justify-end">
            <Button variant="ghost" onClick={onClose}>Cerrar</Button>
          </div>
        </div>
      </div>
    </div>
  )
}
