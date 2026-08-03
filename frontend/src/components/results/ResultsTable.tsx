import Button from '../Button'
import type { BatchResult } from '../../types'
import { bestLangLabel } from '../../utils/format'

interface Props {
  results: BatchResult[]
  onDownload: () => void
}

export default function ResultsTable({ results, onDownload }: Props) {
  if (results.length === 0) return null

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Resultados ({results.length} intenciones por producto)</span>
        <Button variant="success" onClick={onDownload}>
          <span className="material-icons text-base">download</span>
          Descargar Excel
        </Button>
      </div>
      <div className="overflow-x-auto">
        <table className="table">
          <thead>
            <tr>
              <th>Producto</th>
              <th>Intención</th>
              <th>Reseña resumen (ES)</th>
              <th>Traducción (EN)</th>
              <th className="text-center">Cant.</th>
              <th className="text-right">Tok. ES</th>
              <th className="text-right">Tok. EN</th>
              <th>Mejor idioma</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r, i) => {
              const starText = '⭐'.repeat(r.stars || 3)
              const best = bestLangLabel(r.best_lang)
              return (
                <tr key={i}>
                  <td className="font-semibold text-[var(--text)]">{r.product_name || 'General'}</td>
                  <td>
                    <div className="font-bold text-amber-400">{starText}</div>
                    <div className="text-xs text-[var(--text-dim)]">({r.stars || 3}/5)</div>
                  </td>
                  <td className="max-w-[280px]">
                    <span className="line-clamp-2" title={r.review}>{r.review}</span>
                  </td>
                  <td className="max-w-[280px]">
                    <span className="line-clamp-2" title={r.text_en}>{r.text_en}</span>
                  </td>
                  <td className="text-center font-bold text-indigo-400">{r.frequency || 1}</td>
                  <td className="text-right tabular-nums">{r.tokens_original}</td>
                  <td className="text-right tabular-nums">{r.tokens_en}</td>
                  <td>
                    <span className={`badge ${r.best_lang === 'en' ? 'bg-emerald-500/15 text-emerald-400' : r.best_lang === 'es' ? 'bg-red-500/15 text-red-400' : 'bg-slate-500/15 text-slate-400'}`}>
                      {best}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
