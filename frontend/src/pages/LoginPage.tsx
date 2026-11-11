import { useState, type FormEvent } from 'react'
import { AppShell } from '../components/AppShell'
import { StatusBanner } from '../components/StatusBanner'
import { useAuth } from '../auth/AuthContext'

interface LoginPageProps {
  onRegister: () => void
  onSuccess: () => void
}

export function LoginPage({ onRegister, onSuccess }: LoginPageProps) {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setBusy(true)
    try {
      await login({ email: email.trim(), password })
      onSuccess()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to sign in.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <AppShell title="Sign in">
      <section className="panel narrow-panel">
        <p className="muted">Sign in with your DME employee account.</p>
        {error ? <StatusBanner tone="error">{error}</StatusBanner> : null}
        <form className="stack-form" onSubmit={handleSubmit}>
          <label className="field">
            <span>Email</span>
            <input
              type="email"
              autoComplete="username"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              disabled={busy}
            />
          </label>
          <label className="field">
            <span>Password</span>
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              disabled={busy}
            />
          </label>
          <button type="submit" className="button button-primary" disabled={busy}>
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        <p className="muted">
          Need an account?{' '}
          <button type="button" className="link-button" onClick={onRegister}>
            Register
          </button>
        </p>
      </section>
    </AppShell>
  )
}
