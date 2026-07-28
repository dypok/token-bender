interface Props {
  title: string
  icon?: string
}

export default function TitleBar({ title, icon = 'auto_awesome' }: Props) {
  return (
    <div className="title-bar">
      <span className="material-icons text-white text-base">{icon}</span>
      <span className="title-bar-text">{title}</span>
      <button className="title-btn" title="Minimize">─</button>
      <button className="title-btn" title="Maximize">□</button>
      <button className="title-btn close" title="Close">✕</button>
    </div>
  )
}
