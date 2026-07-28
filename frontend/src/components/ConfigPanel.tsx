import { useEffect, useState } from 'react'
import { useStore } from '../store/useStore'
import { getConfigStatus } from '../api/client'
import TitleBar from './TitleBar'
import Button from './Button'
import type { ConfigStatus } from '../types'

export default function ConfigPanel() {
  const { deeplApiKey, setDeeplApiKey, engine, setEngine } = useStore()
  const [status, setStatus] = useState<ConfigStatus | null>(null)
  const [localKey, setLocalKey] = useState(deeplApiKey)

  useEffect(() => {
    getConfigStatus().then(setStatus).catch(() => setStatus(null))
  }, [])

  const handleSave = () => {
    setDeeplApiKey(localKey)
  }

  return (
    <div className="window w-[600px]">
      <TitleBar title="Settings" icon="settings" />
      <div className="p-4 space-y-4">
        {/* Engine status */}
        <div className="panel">
          <div className="panel-header">Engine Status</div>
          <div className="text-xs space-y-1">
            <div className="flex items-center gap-2">
              <span className={`material-icons text-sm ${status?.ollama_available ? 'text-green-600' : 'text-red-500'}`}>
                {status?.ollama_available ? 'check_circle' : 'error'}
              </span>
              Ollama: {status?.ollama_available ? 'Running' : 'Not available'}
            </div>
            <div className="flex items-center gap-2">
              <span className={`material-icons text-sm ${localKey ? 'text-green-600' : 'text-gray-400'}`}>
                {localKey ? 'check_circle' : 'radio_button_unchecked'}
              </span>
              DeepL: {localKey ? 'Key set' : 'No API key'}
            </div>
          </div>
        </div>

        {/* DeepL API Key */}
        <div className="panel">
          <div className="panel-header">DeepL API Key</div>
          <div className="flex gap-2 items-center">
            <input
              className="input-aero flex-1"
              type="password"
              value={localKey}
              onChange={(e) => setLocalKey(e.target.value)}
              placeholder="Enter your DeepL API key..."
            />
            <Button onClick={handleSave}>Save</Button>
          </div>
          <p className="text-xs text-gray-500 mt-1">Stored in your browser (localStorage).</p>
        </div>

        {/* Default engine */}
        <div className="panel">
          <div className="panel-header">Default Engine</div>
          <select
            className="input-aero text-xs w-full"
            value={engine}
            onChange={(e) => setEngine(e.target.value as 'ollama' | 'deepl')}
          >
            <option value="ollama">Ollama (local, free)</option>
            <option value="deepl">DeepL (remote, requires API key)</option>
          </select>
        </div>
      </div>
    </div>
  )
}
