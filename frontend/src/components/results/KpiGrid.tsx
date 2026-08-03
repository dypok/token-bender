import type { EconomicSummary } from '../../types'
import { fmtMoney, fmtInt } from '../../utils/format'

function Kpi({ label, value, sub, tone = 'default' }: {
  label: string
  value: string
  sub?: string
  tone?: 'default' | 'success' | 'danger' | 'accent'
}) {
  const color = tone === 'success' ? 'text-emerald-400'
    : tone === 'danger' ? 'text-red-400'
    : tone === 'accent' ? 'text-indigo-400'
    : 'text-[var(--text)]'
  return (
    <div className="kpi">
      <div className="kpi-label">{label}</div>
      <div className={`kpi-value ${color}`}>{value}</div>
      {sub && <div className="mt-1 text-[11px] text-[var(--text-dim)]">{sub}</div>}
    </div>
  )
}

interface Props {
  summary: EconomicSummary
  clusterCount: number
}

export default function KpiGrid({ summary, clusterCount }: Props) {
  const annual = summary.monthly_savings_10k * 12

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
      <Kpi label="Reseñas procesadas" value={fmtInt(summary.total_reviews)} sub={`${clusterCount} intenciones agrupadas`} tone="accent" />
      <Kpi label="Ahorro diario" value={fmtMoney(summary.daily_savings_10k)} sub="a 10k reseñas/día" tone="success" />
      <Kpi label="Ahorro semanal" value={fmtMoney(summary.weekly_savings_10k)} sub="a 10k reseñas/día" />
      <Kpi label="Ahorro mensual" value={fmtMoney(summary.monthly_savings_10k)} sub="a 10k reseñas/día" />
      <Kpi label="Ahorro anual" value={fmtMoney(annual)} sub="a 10k reseñas/día" tone="success" />
    </div>
  )
}
