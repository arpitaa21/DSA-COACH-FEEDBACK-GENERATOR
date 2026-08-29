import { useState } from 'react'
import { login, register } from '../auth.js'
import ThemeToggle from './ThemeToggle.jsx'

export default function Login({ theme, setTheme, onAuthed }) {
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const data = mode === 'login'
        ? await login(username, password)
        : await register(username, password)
      onAuthed(data.username)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex items-center justify-between px-6 md:px-10 py-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-ink-900 dark:bg-amber-400 flex items-center justify-center font-mono font-800 text-amber-400 dark:text-ink-950 text-sm">
            {'</>'}
          </div>
          <p className="font-mono font-bold text-lg tracking-tight leading-none">
            DSA<span className="text-amber-500">Coach</span>
          </p>
        </div>
        <ThemeToggle theme={theme} setTheme={setTheme} />
      </header>

      <div className="flex-1 flex items-center justify-center px-6">
        <div className="w-full max-w-sm">
          <p className="text-[11px] font-mono uppercase tracking-[0.18em] text-ink-600 dark:text-paper-200/60 mb-2">
            Mind Matrix &middot; GENAICH-010
          </p>
          <h1 className="font-mono text-2xl font-extrabold tracking-tight mb-1">
            {mode === 'login' ? 'Log in to track your streak' : 'Create your account'}
          </h1>
          <p className="text-sm text-ink-600 dark:text-paper-200/60 mb-6">
            Every solve is logged to your own account, so your daily-practice streak is
            always yours - not shared with anyone else.
          </p>

          <form onSubmit={handleSubmit} className="panel p-5">
            <label className="block mb-4">
              <span className="block text-xs font-mono uppercase tracking-wider text-ink-600 dark:text-paper-200/60 mb-1.5">
                Username
              </span>
              <input
                required
                autoFocus
                minLength={3}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="your_username"
                className="w-full rounded-lg border border-paper-200 dark:border-ink-600 bg-paper-50 dark:bg-ink-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400/60"
              />
            </label>

            <label className="block mb-2">
              <span className="block text-xs font-mono uppercase tracking-wider text-ink-600 dark:text-paper-200/60 mb-1.5">
                Password
              </span>
              <input
                required
                type="password"
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 6 characters"
                className="w-full rounded-lg border border-paper-200 dark:border-ink-600 bg-paper-50 dark:bg-ink-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400/60"
              />
            </label>

            {error && (
              <p className="text-xs text-coral-400 mt-2 mb-1">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-4 py-3 rounded-xl font-mono font-bold text-sm bg-ink-900 text-amber-400 dark:bg-amber-400 dark:text-ink-950 hover:opacity-90 disabled:opacity-40 transition-opacity"
            >
              {loading ? 'Please wait…' : mode === 'login' ? 'Log in →' : 'Create account →'}
            </button>
          </form>

          <p className="text-xs text-center mt-4 text-ink-600 dark:text-paper-200/60">
            {mode === 'login' ? "Don't have an account?" : 'Already have an account?'}{' '}
            <button
              type="button"
              className="text-amber-500 font-medium hover:underline"
              onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(null) }}
            >
              {mode === 'login' ? 'Create one' : 'Log in'}
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}
