import { useState } from 'react'
import ExcelIngest from './components/ExcelIngest'
import ConfigPanel from './components/ConfigPanel'

export default function App() {
  const [configOpen, setConfigOpen] = useState(false)

  return (
    <div className="min-h-screen">
      {/* Navbar */}
      <header className="sticky top-0 z-40 border-b border-[var(--border)] bg-[rgba(11,17,32,0.85)] backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-400 shadow-lg shadow-indigo-500/30">
              <span className="material-icons text-white text-lg">bolt</span>
            </div>
            <div>
              <div className="text-sm font-bold tracking-tight">Token Bender</div>
              <div className="text-[11px] text-[var(--text-dim)]">Análisis de reseñas &amp; ahorro de tokens</div>
            </div>
          </div>
          <button
            className="btn btn-ghost"
            onClick={() => setConfigOpen(true)}
          >
            <span className="material-icons text-base">settings</span>
            Configuración
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        <ExcelIngest />
      </main>

      {configOpen && <ConfigPanel onClose={() => setConfigOpen(false)} />}
    </div>
  )
}
