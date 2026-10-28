import { useState, useMemo } from 'react'
import { login, register } from '../auth.js'
import ThemeToggle from './ThemeToggle.jsx'

export default function Login({ theme, setTheme, onAuthed }) {
  const [mode, setMode] = useState('login') // 'login' | 'register'

  // Login form state
  const [loginIdentifier, setLoginIdentifier] = useState('')
  const [loginPassword, setLoginPassword] = useState('')
  const [showLoginPassword, setShowLoginPassword] = useState(false)

  // Registration form state
  const [regUsername, setRegUsername] = useState('')
  const [regEmail, setRegEmail] = useState('')
  const [regDisplayName, setRegDisplayName] = useState('')
  const [regPassword, setRegPassword] = useState('')
  const [regConfirmPassword, setRegConfirmPassword] = useState('')
  const [showRegPassword, setShowRegPassword] = useState(false)
  const [showRegConfirmPassword, setShowRegConfirmPassword] = useState(false)

  // Feedback & status state
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [loading, setLoading] = useState(false)
  const [touched, setTouched] = useState({})

  // Password strength evaluation
  const passwordChecks = useMemo(() => {
    return {
      minLength: regPassword.length >= 8,
      hasLower: /[a-z]/.test(regPassword),
      hasUpper: /[A-Z]/.test(regPassword),
      hasNumber: /\d/.test(regPassword),
      hasSpecial: /[!@#$%^&*(),.?":{}|<>\-_+=\[\]\\/`~]/.test(regPassword),
    }
  }, [regPassword])

  const strengthScore = useMemo(() => {
    let score = 0
    if (passwordChecks.minLength) score += 1
    if (passwordChecks.hasLower) score += 1
    if (passwordChecks.hasUpper) score += 1
    if (passwordChecks.hasNumber) score += 1
    if (passwordChecks.hasSpecial) score += 1
    return score
  }, [passwordChecks])

  const strengthMeta = useMemo(() => {
    if (!regPassword) return { label: '', color: 'bg-paper-200 dark:bg-ink-700', width: '0%' }
    if (strengthScore <= 2) return { label: 'Weak', color: 'bg-coral-400', width: '25%' }
    if (strengthScore === 3) return { label: 'Fair', color: 'bg-amber-500', width: '50%' }
    if (strengthScore === 4) return { label: 'Good', color: 'bg-amber-400', width: '75%' }
    return { label: 'Strong', color: 'bg-teal-400', width: '100%' }
  }, [strengthScore, regPassword])

  // Email format validation
  const isValidEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())

  // Username validation
  const isValidUsername = (uname) => /^[a-zA-Z0-9_-]{3,30}$/.test(uname.trim())

  function handleTouch(field) {
    setTouched((prev) => ({ ...prev, [field]: true }))
  }

  function switchMode(newMode) {
    setMode(newMode)
    setError(null)
    setSuccess(null)
    setTouched({})
  }

  async function handleLoginSubmit(e) {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    if (!loginIdentifier.trim() || !loginPassword) {
      setError('Please provide your username/email and password.')
      return
    }

    setLoading(true)
    try {
      const data = await login(loginIdentifier.trim(), loginPassword)
      setSuccess('Logged in successfully! Redirecting...')
      setTimeout(() => {
        onAuthed(data.username)
      }, 300)
    } catch (err) {
      setError(err.message || 'Invalid username/email or password.')
    } finally {
      setLoading(false)
    }
  }

  async function handleQuickDemoLogin(uname = 'test_dev') {
    setError(null)
    setSuccess(null)
    setLoading(true)
    try {
      const data = await login(uname, 'Password123!')
      setSuccess(`Signed in as ${data.display_name || uname}! Redirecting...`)
      setTimeout(() => {
        onAuthed(data.username)
      }, 200)
    } catch (err) {
      setError(err.message || 'Demo login failed. Please check that the backend is running on port 8000.')
    } finally {
      setLoading(false)
    }
  }

  async function handleRegisterSubmit(e) {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    // Mark all as touched
    setTouched({
      username: true,
      email: true,
      password: true,
      confirmPassword: true,
    })

    // Frontend validations
    if (!isValidUsername(regUsername)) {
      setError('Username must be 3-30 characters (letters, numbers, hyphens, underscores).')
      return
    }

    if (!isValidEmail(regEmail)) {
      setError('Please enter a valid email address (e.g. dev@example.com).')
      return
    }

    if (regPassword.length < 6) {
      setError('Password must be at least 6 characters long.')
      return
    }

    if (regPassword !== regConfirmPassword) {
      setError('Passwords do not match. Please verify and try again.')
      return
    }

    setLoading(true)
    try {
      const data = await register({
        username: regUsername.trim(),
        email: regEmail.trim(),
        password: regPassword,
        displayName: regDisplayName.trim() || undefined,
      })

      setSuccess('Account created successfully! Welcome to DSA Coach.')
      setTimeout(() => {
        onAuthed(data.username)
      }, 400)
    } catch (err) {
      setError(err.message || 'Failed to create account. Please check your details.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-paper-50 dark:bg-ink-950 text-ink-900 dark:text-paper-100 transition-colors">
      {/* Top Header */}
      <header className="flex items-center justify-between px-6 md:px-10 py-5 border-b border-paper-200/60 dark:border-ink-800">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-ink-900 dark:bg-amber-400 flex items-center justify-center font-mono font-extrabold text-amber-400 dark:text-ink-950 text-sm shadow-sm">
            {'</>'}
          </div>
          <div>
            <p className="font-mono font-bold text-lg tracking-tight leading-none">
              DSA<span className="text-amber-500">Coach</span>
            </p>
            <p className="text-[10px] uppercase font-mono tracking-[0.16em] text-ink-600 dark:text-paper-200/50 mt-1">
              Mind Matrix &middot; GENAICH-010
            </p>
          </div>
        </div>
        <ThemeToggle theme={theme} setTheme={setTheme} />
      </header>

      {/* Main Container */}
      <div className="flex-1 flex items-center justify-center px-3.5 sm:px-4 py-5 sm:py-8">
        <div className="w-full max-w-md">
          {/* Header Title */}
          <div className="text-center mb-5 sm:mb-6">
            <h1 className="font-mono text-xl sm:text-2xl md:text-3xl font-extrabold tracking-tight mb-1.5 sm:mb-2">
              {mode === 'login' ? 'Welcome Back' : 'Create an Account'}
            </h1>
            <p className="text-xs md:text-sm text-ink-600 dark:text-paper-200/70 max-w-sm mx-auto">
              {mode === 'login'
                ? 'Sign in to access your practice history and maintain your daily DSA streak.'
                : 'Join DSA Coach to track personalized progress and get AI feedback on your code.'}
            </p>
          </div>

          {/* Card Container */}
          <div className="panel p-4 sm:p-6 shadow-md border border-paper-200 dark:border-ink-700">
            {/* Mode Tabs */}
            <div className="flex rounded-xl bg-paper-100 dark:bg-ink-800 p-1 mb-6 font-mono text-xs font-semibold">
              <button
                type="button"
                onClick={() => switchMode('login')}
                className={`flex-1 py-2 rounded-lg transition-all text-center ${
                  mode === 'login'
                    ? 'bg-white dark:bg-ink-900 text-ink-950 dark:text-amber-400 shadow-sm'
                    : 'text-ink-600 dark:text-paper-200/60 hover:text-ink-900 dark:hover:text-paper-100'
                }`}
              >
                Log In
              </button>
              <button
                type="button"
                onClick={() => switchMode('register')}
                className={`flex-1 py-2 rounded-lg transition-all text-center ${
                  mode === 'register'
                    ? 'bg-white dark:bg-ink-900 text-ink-950 dark:text-amber-400 shadow-sm'
                    : 'text-ink-600 dark:text-paper-200/60 hover:text-ink-900 dark:hover:text-paper-100'
                }`}
              >
                Create Account
              </button>
            </div>

            {/* Error Notification */}
            {error && (
              <div
                role="alert"
                className="mb-5 p-3.5 rounded-xl bg-coral-400/10 border border-coral-400/40 text-coral-400 text-xs flex items-start gap-2.5 leading-relaxed"
              >
                <span className="font-bold text-sm leading-none mt-0.5">✕</span>
                <span className="flex-1 font-medium">{error}</span>
              </div>
            )}

            {/* Success Notification */}
            {success && (
              <div
                role="status"
                className="mb-5 p-3.5 rounded-xl bg-teal-400/10 border border-teal-400/40 text-teal-400 text-xs flex items-start gap-2.5 leading-relaxed"
              >
                <span className="font-bold text-sm leading-none mt-0.5">✓</span>
                <span className="flex-1 font-medium">{success}</span>
              </div>
            )}

            {/* LOGIN FORM */}
            {mode === 'login' ? (
              <form onSubmit={handleLoginSubmit} noValidate className="space-y-4">
                <label className="block">
                  <span className="block text-xs font-mono uppercase tracking-wider text-ink-600 dark:text-paper-200/70 mb-1.5 font-semibold">
                    Username or Email
                  </span>
                  <input
                    type="text"
                    required
                    autoFocus
                    autoComplete="username"
                    value={loginIdentifier}
                    onChange={(e) => setLoginIdentifier(e.target.value)}
                    placeholder="e.g. alex_coder or alex@example.com"
                    className="w-full rounded-xl border border-paper-200 dark:border-ink-600 bg-paper-50 dark:bg-ink-800 px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400/70 transition"
                  />
                </label>

                <label className="block">
                  <div className="flex justify-between items-center mb-1.5">
                    <span className="text-xs font-mono uppercase tracking-wider text-ink-600 dark:text-paper-200/70 font-semibold">
                      Password
                    </span>
                  </div>
                  <div className="relative">
                    <input
                      type={showLoginPassword ? 'text' : 'password'}
                      required
                      autoComplete="current-password"
                      value={loginPassword}
                      onChange={(e) => setLoginPassword(e.target.value)}
                      placeholder="Enter your password"
                      className="w-full rounded-xl border border-paper-200 dark:border-ink-600 bg-paper-50 dark:bg-ink-800 px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400/70 transition pr-10"
                    />
                    <button
                      type="button"
                      tabIndex={-1}
                      onClick={() => setShowLoginPassword(!showLoginPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-mono text-ink-600 dark:text-paper-200/50 hover:text-amber-500"
                    >
                      {showLoginPassword ? 'Hide' : 'Show'}
                    </button>
                  </div>
                </label>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full mt-2 py-3 rounded-xl font-mono font-bold text-sm bg-ink-900 text-amber-400 dark:bg-amber-400 dark:text-ink-950 hover:opacity-90 disabled:opacity-50 transition shadow-sm flex items-center justify-center gap-2 cursor-pointer"
                >
                  {loading ? (
                    <>
                      <span className="inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                      <span>Verifying credentials…</span>
                    </>
                  ) : (
                    <span>Sign In →</span>
                  )}
                </button>

                {/* Quick 1-Click Demo Login */}
                <div className="pt-2">
                  <button
                    type="button"
                    disabled={loading}
                    onClick={() => handleQuickDemoLogin('test_dev')}
                    className="w-full py-2.5 rounded-xl font-mono font-semibold text-xs border border-amber-500/40 bg-amber-400/10 text-amber-500 hover:bg-amber-400/20 transition flex items-center justify-center gap-2 cursor-pointer"
                  >
                    <span>⚡ Quick 1-Click Demo Login (test_dev)</span>
                  </button>
                </div>

                {/* Quick Credentials Helpers */}
                <div className="p-3 rounded-xl bg-paper-100 dark:bg-ink-800/80 border border-paper-200 dark:border-ink-700 text-xs">
                  <div className="flex items-center justify-between font-mono mb-1.5">
                    <span className="font-semibold text-ink-600 dark:text-paper-200/70">Test Accounts</span>
                    <span className="text-[10px] text-ink-600/60 dark:text-paper-200/40">Click to autofill</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => { setLoginIdentifier('test_dev'); setLoginPassword('Password123!'); }}
                      className="px-2.5 py-1 rounded bg-white dark:bg-ink-700 border border-paper-200 dark:border-ink-600 font-mono text-[11px] text-ink-800 dark:text-paper-100 hover:text-amber-500 hover:border-amber-400 transition cursor-pointer"
                    >
                      test_dev
                    </button>
                    <button
                      type="button"
                      onClick={() => { setLoginIdentifier('arpitaa21'); setLoginPassword('Password123!'); }}
                      className="px-2.5 py-1 rounded bg-white dark:bg-ink-700 border border-paper-200 dark:border-ink-600 font-mono text-[11px] text-ink-800 dark:text-paper-100 hover:text-amber-500 hover:border-amber-400 transition cursor-pointer"
                    >
                      arpitaa21
                    </button>
                  </div>
                </div>
              </form>
            ) : (
              /* CREATE ACCOUNT FORM */
              <form onSubmit={handleRegisterSubmit} noValidate className="space-y-4">
                {/* Display Name (Optional) */}
                <label className="block">
                  <span className="block text-xs font-mono uppercase tracking-wider text-ink-600 dark:text-paper-200/70 mb-1.5 font-semibold">
                    Display Name <span className="text-[10px] lowercase text-ink-600/60 dark:text-paper-200/40 font-normal">(optional)</span>
                  </span>
                  <input
                    type="text"
                    value={regDisplayName}
                    onChange={(e) => setRegDisplayName(e.target.value)}
                    placeholder="e.g. Alex Rivera"
                    autoComplete="name"
                    className="w-full rounded-xl border border-paper-200 dark:border-ink-600 bg-paper-50 dark:bg-ink-800 px-3.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400/70 transition"
                  />
                </label>

                {/* Username */}
                <label className="block">
                  <div className="flex justify-between items-center mb-1.5">
                    <span className="text-xs font-mono uppercase tracking-wider text-ink-600 dark:text-paper-200/70 font-semibold">
                      Username <span className="text-coral-400">*</span>
                    </span>
                    {touched.username && !isValidUsername(regUsername) && (
                      <span className="text-[11px] text-coral-400 font-mono">3-30 letters/numbers</span>
                    )}
                    {touched.username && isValidUsername(regUsername) && (
                      <span className="text-[11px] text-teal-400 font-mono">✓ Valid</span>
                    )}
                  </div>
                  <input
                    type="text"
                    required
                    autoComplete="username"
                    value={regUsername}
                    onBlur={() => handleTouch('username')}
                    onChange={(e) => setRegUsername(e.target.value)}
                    placeholder="e.g. alex_coder"
                    className={`w-full rounded-xl border px-3.5 py-2 text-sm focus:outline-none focus:ring-2 transition ${
                      touched.username && !isValidUsername(regUsername)
                        ? 'border-coral-400/80 bg-coral-400/5 focus:ring-coral-400/50'
                        : 'border-paper-200 dark:border-ink-600 bg-paper-50 dark:bg-ink-800 focus:ring-amber-400/70'
                    }`}
                  />
                </label>

                {/* Email Address */}
                <label className="block">
                  <div className="flex justify-between items-center mb-1.5">
                    <span className="text-xs font-mono uppercase tracking-wider text-ink-600 dark:text-paper-200/70 font-semibold">
                      Email Address <span className="text-coral-400">*</span>
                    </span>
                    {touched.email && !isValidEmail(regEmail) && (
                      <span className="text-[11px] text-coral-400 font-mono">Invalid format</span>
                    )}
                    {touched.email && isValidEmail(regEmail) && (
                      <span className="text-[11px] text-teal-400 font-mono">✓ Valid</span>
                    )}
                  </div>
                  <input
                    type="email"
                    required
                    autoComplete="email"
                    value={regEmail}
                    onBlur={() => handleTouch('email')}
                    onChange={(e) => setRegEmail(e.target.value)}
                    placeholder="e.g. alex@example.com"
                    className={`w-full rounded-xl border px-3.5 py-2 text-sm focus:outline-none focus:ring-2 transition ${
                      touched.email && !isValidEmail(regEmail)
                        ? 'border-coral-400/80 bg-coral-400/5 focus:ring-coral-400/50'
                        : 'border-paper-200 dark:border-ink-600 bg-paper-50 dark:bg-ink-800 focus:ring-amber-400/70'
                    }`}
                  />
                </label>

                {/* Password */}
                <div className="block">
                  <div className="flex justify-between items-center mb-1.5">
                    <span className="text-xs font-mono uppercase tracking-wider text-ink-600 dark:text-paper-200/70 font-semibold">
                      Password <span className="text-coral-400">*</span>
                    </span>
                    {strengthMeta.label && (
                      <span
                        className={`text-[11px] font-mono font-bold ${
                          strengthScore <= 2
                            ? 'text-coral-400'
                            : strengthScore <= 4
                            ? 'text-amber-500'
                            : 'text-teal-400'
                        }`}
                      >
                        {strengthMeta.label}
                      </span>
                    )}
                  </div>
                  <div className="relative">
                    <input
                      type={showRegPassword ? 'text' : 'password'}
                      required
                      autoComplete="new-password"
                      value={regPassword}
                      onBlur={() => handleTouch('password')}
                      onChange={(e) => setRegPassword(e.target.value)}
                      placeholder="Create a strong password"
                      className="w-full rounded-xl border border-paper-200 dark:border-ink-600 bg-paper-50 dark:bg-ink-800 px-3.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400/70 transition pr-10"
                    />
                    <button
                      type="button"
                      tabIndex={-1}
                      onClick={() => setShowRegPassword(!showRegPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-mono text-ink-600 dark:text-paper-200/50 hover:text-amber-500"
                    >
                      {showRegPassword ? 'Hide' : 'Show'}
                    </button>
                  </div>

                  {/* Password Strength Meter Bar */}
                  {regPassword && (
                    <div className="mt-2">
                      <div className="w-full h-1.5 bg-paper-200 dark:bg-ink-700 rounded-full overflow-hidden">
                        <div
                          className={`h-full transition-all duration-300 rounded-full ${strengthMeta.color}`}
                          style={{ width: strengthMeta.width }}
                        />
                      </div>

                      {/* Password Requirements Checklist */}
                      <div className="mt-2.5 grid grid-cols-1 sm:grid-cols-2 gap-1 text-[11px] font-mono text-ink-600 dark:text-paper-200/70">
                        <div className={`flex items-center gap-1.5 ${passwordChecks.minLength ? 'text-teal-400 font-semibold' : ''}`}>
                          <span>{passwordChecks.minLength ? '✓' : '○'}</span> 8+ characters
                        </div>
                        <div className={`flex items-center gap-1.5 ${passwordChecks.hasUpper ? 'text-teal-400 font-semibold' : ''}`}>
                          <span>{passwordChecks.hasUpper ? '✓' : '○'}</span> Uppercase letter
                        </div>
                        <div className={`flex items-center gap-1.5 ${passwordChecks.hasLower ? 'text-teal-400 font-semibold' : ''}`}>
                          <span>{passwordChecks.hasLower ? '✓' : '○'}</span> Lowercase letter
                        </div>
                        <div className={`flex items-center gap-1.5 ${passwordChecks.hasNumber ? 'text-teal-400 font-semibold' : ''}`}>
                          <span>{passwordChecks.hasNumber ? '✓' : '○'}</span> Number (0-9)
                        </div>
                        <div className={`col-span-1 sm:col-span-2 flex items-center gap-1.5 ${passwordChecks.hasSpecial ? 'text-teal-400 font-semibold' : ''}`}>
                          <span>{passwordChecks.hasSpecial ? '✓' : '○'}</span> Special character (!@#$%^&*)
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Confirm Password */}
                <label className="block">
                  <div className="flex justify-between items-center mb-1.5">
                    <span className="text-xs font-mono uppercase tracking-wider text-ink-600 dark:text-paper-200/70 font-semibold">
                      Confirm Password <span className="text-coral-400">*</span>
                    </span>
                    {touched.confirmPassword && regPassword && regConfirmPassword && (
                      regPassword === regConfirmPassword ? (
                        <span className="text-[11px] text-teal-400 font-mono">✓ Match</span>
                      ) : (
                        <span className="text-[11px] text-coral-400 font-mono">Does not match</span>
                      )
                    )}
                  </div>
                  <div className="relative">
                    <input
                      type={showRegConfirmPassword ? 'text' : 'password'}
                      required
                      autoComplete="new-password"
                      value={regConfirmPassword}
                      onBlur={() => handleTouch('confirmPassword')}
                      onChange={(e) => setRegConfirmPassword(e.target.value)}
                      placeholder="Repeat your password"
                      className={`w-full rounded-xl border px-3.5 py-2 text-sm focus:outline-none focus:ring-2 transition pr-10 ${
                        touched.confirmPassword && regPassword !== regConfirmPassword
                          ? 'border-coral-400/80 bg-coral-400/5 focus:ring-coral-400/50'
                          : 'border-paper-200 dark:border-ink-600 bg-paper-50 dark:bg-ink-800 focus:ring-amber-400/70'
                      }`}
                    />
                    <button
                      type="button"
                      tabIndex={-1}
                      onClick={() => setShowRegConfirmPassword(!showRegConfirmPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-mono text-ink-600 dark:text-paper-200/50 hover:text-amber-500"
                    >
                      {showRegConfirmPassword ? 'Hide' : 'Show'}
                    </button>
                  </div>
                </label>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full mt-2 py-3 rounded-xl font-mono font-bold text-sm bg-ink-900 text-amber-400 dark:bg-amber-400 dark:text-ink-950 hover:opacity-90 disabled:opacity-50 transition shadow-sm flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <span className="inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                      <span>Creating Account…</span>
                    </>
                  ) : (
                    <span>Complete Registration →</span>
                  )}
                </button>
              </form>
            )}
          </div>

          {/* Toggle bottom link */}
          <p className="text-xs text-center mt-5 text-ink-600 dark:text-paper-200/70">
            {mode === 'login' ? "Don't have an account yet?" : 'Already registered?'}{' '}
            <button
              type="button"
              className="text-amber-500 font-semibold hover:underline cursor-pointer"
              onClick={() => switchMode(mode === 'login' ? 'register' : 'login')}
            >
              {mode === 'login' ? 'Create an Account' : 'Sign in to existing account'}
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}
