interface Props {
  loading: boolean
  message?: string
}

export default function StatusBar({ loading, message }: Props) {
  if (!loading && !message) return null
  return (
    <div className="mt-3">
      {loading && (
        <div className="progress-glass">
          <div className="progress-glass-fill" style={{ width: '60%' }} />
        </div>
      )}
      {message && <div className="tooltip mt-1 inline-block">{message}</div>}
    </div>
  )
}
