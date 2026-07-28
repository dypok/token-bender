import MainWindow from './components/MainWindow'
import ConfigPanel from './components/ConfigPanel'
import ExcelIngest from './components/ExcelIngest'
import ProjectionPanel from './components/ProjectionPanel'
import { useStore } from './store/useStore'

function NavItem({ label, panel, icon }: { label: string; panel: string; icon: string }) {
  const { activePanel, setActivePanel } = useStore()
  const isActive = activePanel === panel
  return (
    <button
      className={`flex items-center gap-2 px-4 py-2 text-xs cursor-pointer border-r border-gray-300 ${
        isActive
          ? 'bg-white font-semibold text-[var(--aero-end)] shadow-inner'
          : 'text-gray-600 hover:bg-gray-200'
      }`}
      onClick={() => setActivePanel(panel as typeof activePanel)}
    >
      <span className="material-icons text-base">{icon}</span>
      {label}
    </button>
  )
}

export default function App() {
  const { activePanel } = useStore()

  return (
    <div className="flex flex-col items-center gap-0 min-h-screen justify-center py-8">
      {/* Taskbar-style navigation */}
      <div className="flex bg-[var(--bg-surface)] border border-gray-300 rounded-t-lg overflow-hidden shadow-sm">
        <NavItem label="Analyze" panel="analyze" icon="auto_awesome" />
        <NavItem label="Settings" panel="config" icon="settings" />
        <NavItem label="Excel Import" panel="excel" icon="description" />
        <NavItem label="Projection" panel="projection" icon="trending_up" />
      </div>

      {/* Panels */}
      {activePanel === 'analyze' && <MainWindow />}
      {activePanel === 'config' && <ConfigPanel />}
      {activePanel === 'excel' && <ExcelIngest />}
      {activePanel === 'projection' && <ProjectionPanel />}
    </div>
  )
}
