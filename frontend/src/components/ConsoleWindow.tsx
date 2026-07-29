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
  white: '#f0f0f0',
  green: '#4af626',
  yellow: '#f5f543',
  red: '#f6544a',
  cyan: '#4af5f6',
  gray: '#888888',
}

export default function ConsoleWindow({ lines, visible, onClose }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [lines])

  if (!visible) return null

  return (
    <div className="border border-gray-600 rounded overflow-hidden shadow-lg" style={{ background: '#0c0c0c' }}>
      {/* Title bar */}
      <div className="flex items-center px-2 py-1 select-none" style={{ background: 'linear-gradient(180deg, #2d4b7a, #1a3057)' }}>
        <span className="text-xs text-white font-bold tracking-wide drop-shadow-[0_1px_1px_rgba(0,0,0,0.6)] flex items-center gap-1.5">
          <span className="text-yellow-300 text-sm">&#9679;</span>
          C:\Windows\system32\cmd.exe
        </span>
        <div className="flex-1" />
        <div className="flex items-center gap-0.5">
          <button className="w-5 h-4 flex items-center justify-center text-xs text-white bg-[rgba(255,255,255,0.1)] border border-[rgba(255,255,255,0.15)] rounded-sm hover:bg-[rgba(255,255,255,0.2)] cursor-pointer">─</button>
          <button className="w-5 h-4 flex items-center justify-center text-xs text-white bg-[rgba(255,255,255,0.1)] border border-[rgba(255,255,255,0.15)] rounded-sm hover:bg-[rgba(255,255,255,0.2)] cursor-pointer">□</button>
          <button onClick={onClose} className="w-5 h-4 flex items-center justify-center text-xs text-white bg-[rgba(220,50,50,0.6)] border border-[rgba(255,100,100,0.2)] rounded-sm hover:bg-[rgba(220,50,50,0.9)] cursor-pointer">✕</button>
        </div>
      </div>

      {/* Console body */}
      <div
        className="overflow-y-auto p-2 font-mono"
        style={{
          background: '#0c0c0c',
          height: '280px',
          fontFamily: '"Consolas", "Lucida Console", "Courier New", monospace',
          fontSize: '12px',
          lineHeight: '1.5',
        }}
      >
        {lines.map((line, i) => (
          <div key={i} style={{ color: COLORS[line.color ?? 'white'] }} className="whitespace-pre-wrap">
            {line.text}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
