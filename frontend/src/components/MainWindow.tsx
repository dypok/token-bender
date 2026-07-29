import { useState } from 'react'
import { useStore } from '../store/useStore'
import { analyzeText } from '../api/client'
import TitleBar from './TitleBar'
import Button from './Button'
import StatusBar from './StatusBar'
import ResultsPanel from './ResultsPanel'

export default function MainWindow() {
  const {
    inputText, setInputText,
    engine, setEngine,
    deeplApiKey,
    loading, setLoading,
    setResult,
    error, setError,
    result,
  } = useStore()

  const [classify, setClassify] = useState(false)

  const handleAnalyze = async () => {
    if (!inputText.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await analyzeText(inputText, engine, deeplApiKey, classify)
      setResult(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="window w-[820px]">
      <TitleBar title="Token Optimizer" icon="auto_awesome" />
      <div className="p-4 space-y-4">
        {/* Input area */}
        <div>
          <label className="text-xs font-semibold text-gray-600 block mb-1">Enter your prompt</label>
          <textarea
            className="input-aero w-full h-28 resize-y"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Paste or type your text here..."
          />
        </div>

        {/* Controls */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-xs font-semibold text-gray-600">Engine:</label>
            <select
              className="input-aero text-xs"
              value={engine}
              onChange={(e) => setEngine(e.target.value as 'ollama' | 'deepl' | 'google' | 'argos')}
            >
              <option value="ollama">Ollama (local)</option>
              <option value="deepl">DeepL (API)</option>
              <option value="google">Google Translate</option>
              <option value="argos">Argos Translate (local)</option>
            </select>
          </div>
          <label className="flex items-center gap-1 text-xs cursor-pointer">
            <input type="checkbox" checked={classify} onChange={(e) => setClassify(e.target.checked)} />
            Classify
          </label>
          <Button onClick={handleAnalyze} disabled={loading || !inputText.trim()}>
            {loading ? 'Analyzing...' : 'Analyze'}
          </Button>
        </div>

        <StatusBar loading={loading} message={error || undefined} />

        {/* Results */}
        {result && <ResultsPanel />}
      </div>
    </div>
  )
}
