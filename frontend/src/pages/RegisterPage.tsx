import { useState, type FormEvent } from 'react'
import { AppShell } from '../components/AppShell'
import { StatusBanner } from '../components/StatusBanner'
import { useAuth } from '../auth/AuthContext'

interface RegisterPageProps {
  onLogin: () => void
  onSuccess: () => void
}

export function RegisterPage({ onLogin, onSuccess }: RegisterPageProps) {
  const { register } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setMessage(null)
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (!/^[a-z0-9_]{3,32}$/.test(username.trim().toLowerCase())) {
      setError('Username must be 3 to 32 letters, numbers, or underscores.')
      return
    }
    setBusy(true)
    try {
      await register({ username: username.trim().toLowerCase(), password })
      setMessage('Account created. You can sign in now.')
      onSuccess()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to register.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <AppShell title="Register">
      <section className="panel narrow-panel">
        <p className="muted">Create a DME employee account to manage order intake.</p>
        {error ? <StatusBanner tone="error">{error}</StatusBanner> : null}
        {message ? <StatusBanner tone="success">{message}</StatusBanner> : null}
        <form className="stack-form" onSubmit={handleSubmit}>
          <label className="field">
            <span>Username</span>
            <input
              type="text"
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
              disabled={busy}
            />
          </label>
          <label className="field">
            <span>Password</span>
            <input
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              minLength={8}
              disabled={busy}
            />
          </label>
          <button type="submit" className="button button-primary" disabled={busy}>
            {busy ? 'Creating account…' : 'Create account'}
          </button>
        </form>
        <p className="muted">
          Already registered?{' '}
          <button type="button" className="link-button" onClick={onLogin}>
            Sign in
          </button>
        </p>
      </section>
    </AppShell>
  )
}
