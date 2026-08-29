export default function ThemeToggle({ theme, setTheme }) {
  const isDark = theme === 'dark'
  return (
    <button
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
      aria-label="Toggle color theme"
      className="relative w-14 h-8 rounded-full bg-paper-200 dark:bg-ink-700 border border-paper-200 dark:border-ink-600 transition-colors"
    >
      <span
        className={`absolute top-0.5 left-0.5 w-6 h-6 rounded-full bg-white dark:bg-amber-400 shadow flex items-center justify-center text-[11px] transition-transform ${isDark ? 'translate-x-6' : 'translate-x-0'}`}
      >
        {isDark ? '🌙' : '☀️'}
      </span>
    </button>
  )
}
