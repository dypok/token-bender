import { useStore } from '../store/useStore'

function VariantCard({ label, text, language, tokenCount, diff }: {
  label: string
  text: string
  language: string
  tokenCount: number
  diff?: number
}) {
  const handleCopy = () => navigator.clipboard.writeText(text)

  return (
    <div className="panel flex-1 flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <span className="font-semibold text-sm text-[#1a3a6a]">{label}</span>
        <span className="text-xs text-gray-500 bg-gray-200 rounded px-1.5 py-0.5">{language}</span>
      </div>
      <div className="text-xs text-gray-700 bg-white rounded p-2 border border-gray-200 flex-1 min-h-[80px] whitespace-pre-wrap">
        {text}
      </div>
      <div className="flex items-center justify-between mt-2 text-xs text-gray-600">
        <span>Tokens: <strong>{tokenCount}</strong></span>
        {diff !== undefined && (
          <span className={diff <= 0 ? 'text-green-600' : 'text-red-600'}>
            {diff > 0 ? `+${diff}` : diff} vs original
          </span>
        )}
        <button
          className="text-[var(--aero-start)] hover:underline cursor-pointer"
          onClick={handleCopy}
        >
          Copy
        </button>
      </div>
    </div>
  )
}

export default function ResultsPanel() {
  const { result, setActivePanel } = useStore()
  if (!result) return null

  const origTokens = result.original.token_count

  return (
    <div>
      <div className="panel-header">Results</div>
      <div className="flex gap-3">
        <VariantCard
          label="Original"
          text={result.original.text}
          language={result.original.language}
          tokenCount={origTokens}
          diff={0}
        />
        <VariantCard
          label="Translated"
          text={result.translated.text}
          language={result.translated.language}
          tokenCount={result.translated.token_count}
          diff={result.translated.token_count - origTokens}
        />
        <VariantCard
          label="Spanglish"
          text={result.spanglish.text}
          language="mix"
          tokenCount={result.spanglish.token_count}
          diff={result.spanglish.token_count - origTokens}
        />
      </div>
      {result.classification && (
        <div className="mt-2 text-xs text-gray-600">
          Classification: error_type=<strong>{result.classification.error_type}</strong>, component=<strong>{result.classification.component}</strong>
          &nbsp;| engine: {result.engine_used}
        </div>
      )}
      <div className="mt-2 flex gap-2">
        <button
          className="text-xs text-[var(--aero-start)] hover:underline cursor-pointer"
          onClick={() => setActivePanel('projection')}
        >
          Open in Projection →
        </button>
      </div>
    </div>
  )
}
