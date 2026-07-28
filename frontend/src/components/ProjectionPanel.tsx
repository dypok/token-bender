import { useState } from 'react'
import { computeProjection } from '../api/client'
import TitleBar from './TitleBar'
import Button from './Button'
import type { ProjectionResponse } from '../types'

export default function ProjectionPanel() {
  const [origTokens, setOrigTokens] = useState(27)
  const [transTokens, setTransTokens] = useState(19)
  const [reviewsPerDay, setReviewsPerDay] = useState(10000)
  const [costPerMillion, setCostPerMillion] = useState(2.5)
  const [days, setDays] = useState(30)
  const [result, setResult] = useState<ProjectionResponse | null>(null)
  const [loading, setLoading] = useState(false)

  const handleCalc = async () => {
    setLoading(true)
    try {
      const data = await computeProjection(origTokens, transTokens, reviewsPerDay, costPerMillion, days)
      setResult(data)
    } catch {
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="window w-[600px]">
      <TitleBar title="Economic Projection" icon="trending_up" />
      <div className="p-4 space-y-4">
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

        {result && (
          <div className="panel">
            <div className="panel-header">Projection Results</div>
            <div className="grid grid-cols-3 gap-3 text-center">
              <div>
                <div className="text-2xl font-bold text-[var(--aero-end)]">{result.daily_token_diff.toLocaleString()}</div>
                <div className="text-xs text-gray-600">Daily token savings</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-[var(--aero-end)]">{result.monthly_token_diff.toLocaleString()}</div>
                <div className="text-xs text-gray-600">Monthly token savings</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-700">${result.monthly_savings_usd.toFixed(2)}</div>
                <div className="text-xs text-gray-600">Monthly savings (USD)</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
