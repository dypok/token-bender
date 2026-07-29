import { create } from 'zustand'
import type { AnalyzeResponse } from '../types'

interface AppState {
  inputText: string
  engine: 'ollama' | 'deepl' | 'google'
  deeplApiKey: string
  loading: boolean
  result: AnalyzeResponse | null
  error: string | null
  activePanel: 'analyze' | 'config' | 'excel' | 'projection'

  setInputText: (text: string) => void
  setEngine: (engine: 'ollama' | 'deepl' | 'google') => void
  setDeeplApiKey: (key: string) => void
  setLoading: (loading: boolean) => void
  setResult: (result: AnalyzeResponse | null) => void
  setError: (error: string | null) => void
  setActivePanel: (panel: 'analyze' | 'config' | 'excel' | 'projection') => void
}

const storedKey = localStorage.getItem('deepl_api_key') || ''
const storedEngine = (localStorage.getItem('preferred_engine') as 'ollama' | 'deepl' | 'google') || 'ollama'

export const useStore = create<AppState>((set) => ({
  inputText: '',
  engine: storedEngine,
  deeplApiKey: storedKey,
  loading: false,
  result: null,
  error: null,
  activePanel: 'analyze',

  setInputText: (text) => set({ inputText: text }),
  setEngine: (engine) => {
    localStorage.setItem('preferred_engine', engine)
    set({ engine })
  },
  setDeeplApiKey: (key) => {
    localStorage.setItem('deepl_api_key', key)
    set({ deeplApiKey: key })
  },
  setLoading: (loading) => set({ loading }),
  setResult: (result) => set({ result }),
  setError: (error) => set({ error }),
  setActivePanel: (panel) => set({ activePanel: panel }),
}))
