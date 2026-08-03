import { useEffect, useRef } from 'react'

export interface ConsoleLine {
  text: string
  color?: 'white' | 'green' | 'yellow' | 'red' | 'cyan' | 'gray'
}

interface Props {
  lines: ConsoleLine[]
  visible: boolean
  onClose?: () => void
}

const COLORS: Record<string, string> = {
  white: '#cbd5e1',
  green: '#4ade80',
  yellow: '#facc15',
  red: '#f87171',
  cyan: '#22d3ee',
  gray: '#64748b',
}

export default function ConsoleWindow({ lines, visible, onClose }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [lines])

  if (!visible) return null

  return (
    <div className="terminal">
      {/* Terminal header */}
      <div className="flex items-center gap-2 border-b border-[#1e293b] px-4 py-2.5">
        <div className="flex gap-1.5">
          <span className="h-3 w-3 rounded-full bg-red-500/80" />
          <span className="h-3 w-3 rounded-full bg-amber-500/80" />
          <span className="h-3 w-3 rounded-full bg-emerald-500/80" />
        </div>
        <span className="ml-2 text-xs font-medium text-slate-400">Procesamiento batch</span>
        <div className="flex-1" />
        <button
          onClick={onClose}
          className="cursor-pointer rounded p-0.5 text-slate-500 hover:bg-slate-800 hover:text-slate-200"
          title="Cerrar"
        >
          <span className="material-icons text-sm">close</span>
        </button>
      </div>

      {/* Terminal body */}
      <div
        className="h-64 overflow-y-auto px-4 py-3 text-[13px] leading-relaxed"
        style={{ background: '#0a0f1c' }}
      >
        {lines.map((line, i) => (
          <div key={i} style={{ color: COLORS[line.color ?? 'white'] }} className="whitespace-pre-wrap font-mono">
            {line.text}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
