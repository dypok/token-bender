import { useState, useEffect } from 'react'
import { computeProjection } from '../api/client'
import { useStore } from '../store/useStore'
import TitleBar from './TitleBar'
import Button from './Button'
import type { ProjectionResponse } from '../types'

export default function ProjectionPanel() {
  const result = useStore((s) => s.result)

  const defaults = {
    orig: result ? result.original.token_count : 27,
    trans: result ? result.translated.token_count : 19,
  }

  const [origTokens, setOrigTokens] = useState(defaults.orig)
  const [transTokens, setTransTokens] = useState(defaults.trans)
  const [reviewsPerDay, setReviewsPerDay] = useState(10000)
  const [costPerMillion, setCostPerMillion] = useState(2.5)
  const [days, setDays] = useState(30)
  const [projResult, setProjResult] = useState<ProjectionResponse | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (result) {
      setOrigTokens(result.original.token_count)
      setTransTokens(result.translated.token_count)
    }
  }, [result])

  const handleCalc = async () => {
    setLoading(true)
    try {
      const data = await computeProjection(origTokens, transTokens, reviewsPerDay, costPerMillion, days)
      setProjResult(data)
    } catch {
      setProjResult(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="window w-[600px]">
      <TitleBar title="Economic Projection" icon="trending_up" />
      <div className="p-4 space-y-4">
        {result && (
          <div className="panel bg-blue-50 border-blue-200">
            <div className="panel-header">Auto-filled from last analysis</div>
            <div className="text-xs text-gray-600">
              Original: <strong>{result.original.token_count}</strong> tokens ({result.original.language}) &middot;
              Translated: <strong>{result.translated.token_count}</strong> tokens ({result.translated.language})
            </div>
          </div>
        )}
        <div className="panel">
          <div className="panel-header">Parameters</div>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="block text-gray-600 mb-1">Original tokens</label>
              <input className="input-aero w-full" type="number" value={origTokens} onChange={(e) => setOrigTokens(Number(e.target.value))} />
            </div>
            <div>
              <label className="block text-gray-600 mb-1">Translated tokens</label>
              <input className="input-aero w-full" type="number" value={transTokens} onChange={(e) => setTransTokens(Number(e.target.value))} />
            </div>
            <div>
              <label className="block text-gray-600 mb-1">Reviews per day</label>
              <input className="input-aero w-full" type="number" value={reviewsPerDay} onChange={(e) => setReviewsPerDay(Number(e.target.value))} />
            </div>
            <div>
              <label className="block text-gray-600 mb-1">Cost per million tokens (USD)</label>
              <input className="input-aero w-full" type="number" step="0.1" value={costPerMillion} onChange={(e) => setCostPerMillion(Number(e.target.value))} />
            </div>
            <div>
              <label className="block text-gray-600 mb-1">Days</label>
              <input className="input-aero w-full" type="number" value={days} onChange={(e) => setDays(Number(e.target.value))} />
            </div>
            <div className="flex items-end">
              <Button onClick={handleCalc} disabled={loading}>
                {loading ? 'Calculating...' : 'Calculate'}
              </Button>
            </div>
          </div>
        </div>

        {projResult && (
          <div className="panel">
            <div className="panel-header">Projection Results</div>
            <div className="grid grid-cols-3 gap-3 text-center">
              <div>
                <div className="text-2xl font-bold text-[var(--aero-end)]">{projResult.daily_token_diff.toLocaleString()}</div>
                <div className="text-xs text-gray-600">Daily token savings</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-[var(--aero-end)]">{projResult.monthly_token_diff.toLocaleString()}</div>
                <div className="text-xs text-gray-600">Monthly token savings</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-700">${projResult.monthly_savings_usd.toFixed(2)}</div>
                <div className="text-xs text-gray-600">Monthly savings (USD)</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
