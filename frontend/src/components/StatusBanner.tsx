interface StatusBannerProps {
  tone?: 'info' | 'success' | 'error'
  children: string
}

export function StatusBanner({ tone = 'info', children }: StatusBannerProps) {
  return (
    <div className={`status-banner status-banner--${tone}`} role="status" aria-live="polite">
      {children}
    </div>
  )
}
