interface Props {
  ratings: Record<string, number>
}

export default function ProductRatings({ ratings }: Props) {
  if (Object.keys(ratings).length === 0) return null

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Rating por producto</span>
      </div>
      <div className="card-body grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        {Object.entries(ratings).map(([prod, rating]) => (
          <div key={prod} className="rounded-xl border border-[var(--border)] bg-[var(--bg-elevated)] p-4 text-center">
            <div className="truncate text-xs font-medium text-[var(--text-muted)]" title={prod}>{prod}</div>
            <div className="mt-2 text-2xl font-bold text-amber-400">{rating.toFixed(2)}</div>
            <div className="mt-1 text-sm">{'⭐'.repeat(Math.round(rating)) || '—'}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
