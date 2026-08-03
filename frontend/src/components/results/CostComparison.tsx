import type { EconomicSummary } from '../../types'
import { fmtMoney } from '../../utils/format'

interface Props {
  summary: EconomicSummary
}

export default function CostComparison({ summary }: Props) {
  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Comparativa de costos</span>
      </div>
      <div className="card-body grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-elevated)] p-4">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-dim)]">Costo diario (original)</div>
          <div className="mt-1 text-2xl font-bold text-red-400">{fmtMoney(summary.daily_cost_original_10k)}</div>
          <div className="mt-1 text-xs text-[var(--text-dim)]">Prom. {summary.avg_tokens_original} tok/res (esp)</div>
        </div>
        <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-elevated)] p-4">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-dim)]">Costo diario (inglés)</div>
          <div className="mt-1 text-2xl font-bold text-emerald-400">{fmtMoney(summary.daily_cost_en_10k)}</div>
          <div className="mt-1 text-xs text-[var(--text-dim)]">Prom. {summary.avg_tokens_en} tok/res (eng)</div>
        </div>
      </div>
    </div>
  )
}
