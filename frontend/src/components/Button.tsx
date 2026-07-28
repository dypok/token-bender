import clsx from 'clsx'

interface Props {
  children: React.ReactNode
  onClick?: () => void
  disabled?: boolean
  className?: string
}

export default function Button({ children, onClick, disabled, className }: Props) {
  return (
    <button className={clsx('btn-aero', className)} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  )
}
