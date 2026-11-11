import type { ReactNode } from 'react'

interface AppShellProps {
  title: string
  actions?: ReactNode
  children: ReactNode
}

export function AppShell({ title, actions, children }: AppShellProps) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="brand">DME Order Intake</p>
          <h1>{title}</h1>
        </div>
        {actions ? <div className="header-actions">{actions}</div> : null}
      </header>
      <main className="app-main">{children}</main>
    </div>
  )
}
