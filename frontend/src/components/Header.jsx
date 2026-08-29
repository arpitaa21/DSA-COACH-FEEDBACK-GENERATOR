import ThemeToggle from './ThemeToggle.jsx'

export default function Header({ theme, setTheme, username, onLogout }) {
  return (
    <header className="flex items-center justify-between px-6 md:px-10 py-5 border-b border-paper-200 dark:border-ink-700">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-ink-900 dark:bg-amber-400 flex items-center justify-center font-mono font-800 text-amber-400 dark:text-ink-950 text-sm">
          {'</>'}
        </div>
        <div>
          <p className="font-mono font-bold text-lg tracking-tight leading-none">
            DSA<span className="text-amber-500">Coach</span>
          </p>
          <p className="text-[11px] uppercase tracking-[0.18em] text-ink-600 dark:text-paper-200/60 leading-none mt-1">
            Mind Matrix &middot; Code Exec Agent
          </p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        {username && (
          <div className="hidden sm:flex items-center gap-2 text-xs font-mono">
            <span className="w-6 h-6 rounded-full bg-amber-400/20 text-amber-500 flex items-center justify-center font-bold">
              {username.charAt(0).toUpperCase()}
            </span>
            <span className="text-ink-600 dark:text-paper-200/70">{username}</span>
            <button
              onClick={onLogout}
              className="ml-1 text-ink-600 dark:text-paper-200/50 hover:text-coral-400 underline decoration-dotted"
            >
              Log out
            </button>
          </div>
        )}
        <ThemeToggle theme={theme} setTheme={setTheme} />
      </div>
    </header>
  )
}
